#!/usr/bin/env python3
"""Conservative rule-based classification of Sofia property listing text.

This is reproducible text classification, not per-listing legal or human verification.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re
from collections import Counter
from pathlib import Path

STAGES = ["green", "act14", "act15", "act16"]
STAGE_PATTERNS = {
    "act16": re.compile(r"(?<!\w)акт\s*(?:(?:обр\.?|образец)\s*)?16(?!\w)|(?<!\w)акт\s+шестнадесет(?!\w)|разрешение\s+за\s+ползване|въвеждане(?:то)?\s+в\s+експлоатация|въведен[ао]?\s+в\s+експлоатация", re.I),
    "act15": re.compile(r"(?<!\w)акт\s*(?:(?:обр\.?|образец)\s*)?15(?!\w)|(?<!\w)акт\s+петнадесет(?!\w)", re.I),
    "act14": re.compile(r"(?<!\w)акт\s*(?:(?:обр\.?|образец)\s*)?14(?!\w)|(?<!\w)акт\s+четиринадесет(?!\w)", re.I),
    "green": re.compile(r"на\s+зелено|зелено\s+строителство|(?:сграда|строителство|проект)\s+на\s+етап\s+проект|в\s+проектна\s+фаза", re.I),
}
FUTURE = re.compile(r"очакван|предстоящ|предстои|планиран|планира\s+се|ще\s+бъде|ще\s+получи|до\s+получаване|срок|прогноз|годин\s+20\d\d|края\s+на\s+20\d\d|преди\s+акт|без\s+(?:акт\s*)?(?:16|15|14)|няма\s+(?:акт\s*)?(?:16|15|14)|не\s+(?:е\s+)?(?:взет|издаден|получен)", re.I)
NEG_OR_HYP = re.compile(r"няма|без|не\s+(?:е\s+)?(?:взет|издаден|получен|достигнат)|очакван|предстоящ|предстои|планиран|ще\s+бъде|може\s+да|срок|до\s+акт|преди\s+акт|за\s+акт|след\s+акт", re.I)
LAND = re.compile(r"\b(?:парцел|земя|урегулиран\s+поземлен|поземлен\s+имот|земеделск[аи]\s+земя)\b", re.I)

# A match is ignored when nearby language marks it as a planned/unachieved milestone,
# an example/comparison, or a denial. Window is deliberately local to avoid over-reading.
def _near(text: str, start: int, end: int, radius: int = 90) -> str:
    return text[max(0, start-radius):min(len(text), end+radius)]

def _snip(text: str, start: int, end: int, radius: int = 75) -> str:
    s=max(0,start-radius); e=min(len(text),end+radius)
    snippet = re.sub(r"(?<!\w)(?:\+359|00359|0)[\s()./-]*\d(?:[\s()./-]*\d){7,}(?!\w)", "[phone redacted]", text[s:e])
    return re.sub(r"\s+", " ", snippet).strip()

def classify_stage(title: str, desc: str, listing: dict) -> tuple[str,list[str]]:
    text = f"{title}\n{desc}"
    search_text=text.translate(str.maketrans({"А":"а","A":"а","a":"а"}))
    if LAND.search(title) and not re.search(r"апартамент|жилищ|сграда|къща", title, re.I):
        return "not_applicable", ["Title identifies a land/parcel listing; construction stage does not apply."]
    candidates=[]; rejected=[]; negatives=set()
    cue_before=re.compile(r"очакван|очаква(?:\s+се)?|предстоящ|предстои|предвижда(?:\s+се)?|заложен[ао]?|планиран|планира\s+се|ще\s+(?:бъде|има|получи|взет|издаден)|не\s+(?:е\s+)?(?:взет|издаден|получен)|до\s+(?:получаване|акт|края|20\d{2}|[0-3]?\d[./-])|подадени\s+документи|срок|прогноз|(?<!\w)преди(?!\w)|(?<!\w)пред\s*$|(?<!\w)след(?:\s+(?:получаване|издаване|акт))?|за\s+акт",re.I)
    # These markers delimit milestone clauses. Future wording/dates for a later
    # milestone (including the permit-to-use synonym) must not erase an earlier attained stage.
    milestone_re=re.compile(r"(?<!\w)акт\s*(?:(?:обр\.?|образец)\s*)?(?:14|15|16)(?!\w)|разрешение\s+за\s+ползване|въвеждане(?:то)?\s+в\s+експлоатация|въведен[ао]?\s+в\s+експлоатация",re.I)
    for stage,pat in STAGE_PATTERNS.items():
        for m in pat.finditer(search_text):
            sn=_snip(text,m.start(),m.end())
            ctx=_near(text,m.start(),m.end(),100)
            local_before=search_text[max(0,m.start()-30):m.start()]
            local_after=search_text[m.end():min(len(search_text),m.end()+30)]
            if re.search(r"\d+\s*%[^.!?]{0,24}(?:при|за)\s*$",local_before,re.I) or re.match(r"\s*(?:при|за)\s*акт?[^.!?]{0,20}\d+\s*%",local_after,re.I):
                rejected.append(f"Excluded payment milestone: {sn}"); continue
            if re.search(r"(?:например|сравнени[ея]\s+с|подобн[аи]\s+имот|друг[аи]?\s+(?:сграда|имот)|оферт[аи]\s+за)",ctx,re.I):
                rejected.append(f"Excluded comparison/other listing: {sn}"); continue
            prev_markers=list(milestone_re.finditer(search_text,0,m.start()))
            next_marker=milestone_re.search(search_text,m.end())
            # Numeric Act 16 followed immediately by its spelled-out permit synonym is one milestone.
            if stage=="act16" and next_marker and re.search(r"разрешение\s+за\s+ползване|въвеждане(?:то)?\s+в\s+експлоатация|въведен[ао]?\s+в\s+експлоатация",next_marker.group(),re.I):
                between=search_text[m.end():next_marker.start()]
                if re.fullmatch(r"[\s/()–—-]*",between):
                    continue
            # Conversely, in “въвеждане в експлоатация (Акт 16)” classify the
            # explicit numbered milestone once, so its following planned cue is seen.
            if stage=="act16" and next_marker and re.search(r"акт\s*(?:(?:обр\\.?|образец)\s*)?16",next_marker.group(),re.I):
                between=search_text[m.end():next_marker.start()]
                if re.fullmatch(r"[\s/()–—-]*",between):
                    continue
            left=prev_markers[-1].end() if prev_markers else max(0,m.start()-100)
            right=next_marker.start() if next_marker else min(len(search_text),m.end()+100)
            before=search_text[max(left,m.start()-70):m.start()]
            after=search_text[m.end():min(right,m.end()+100)]
            # Cues only count when they attach to this milestone in its local clause.
            prev_cues=[c for c in cue_before.finditer(before) if len(before)-c.end()<=40]
            future_before=bool(prev_cues) and not re.search(r"[.!?\n][^.!?\n]*$",before[prev_cues[-1].end():])
            post_cue=re.search(r"очакван|очаква(?:\s+се)?|предстоящ|предстои|предвижда(?:\s+се)?|заложен[ао]?|планиран|планира\s+се|до\s+(?:получаване|акт|края|20\d{2}|[0-3]?\d[./-])|срок|прогноз",after,re.I)
            future_after=bool(post_cue) and post_cue.start()<=20 and not re.search(r"[.!?\n]",after[:post_cue.start()])
            # A future cue followed by another explicit milestone refers to that later marker.
            if future_after and next_marker:
                between=search_text[m.end():next_marker.start()]
                cue_match=re.search(r"очакван|очаква(?:\s+се)?|предстоящ|предстои|предвижда(?:\s+се)?|заложен[ао]?|планиран|планира\s+се|до\s+(?:получаване|акт|края|20\d{2}|[0-3]?\d[./-])|срок|прогноз",between,re.I)
                if cue_match: future_after=False
            year=re.search(r"20(?:2[7-9]|[3-9]\d)",after)
            late_match=re.search(r"(?:ноември|декември|края\s+на\s*2026|2026\s*г?\.?\s*(?:ноември|декември))",after,re.I)
            date_match=year or late_match
            date_prefix=after[:date_match.start()] if date_match else ""
            nonspecific_future_work=bool(re.search(r"завършен|довърш|ремонт|обзавед|готов|завършване",date_prefix,re.I))
            historical_year_nearby=bool(re.search(r"(?:акт\s*16|разрешение\s+за\s+ползване)\s+от\s+19\d{2}",before[-20:]+after[:20],re.I))
            dated_future=bool(date_match) and len(date_prefix)<=40 and not nonspecific_future_work and not historical_year_nearby
            # A standalone year/date only marks the milestone immediately attached to it.
            deadline=bool(re.search(r"срок",before[-40:],re.I))
            neg=re.search(r"(?:няма|без|не\s+(?:е\s+)?(?:взет|издаден|получен))\s*$",before[-24:],re.I)
            payment=bool(re.search(r"\d+\s*%[^.!?]{0,15}(?:при|за)\s*$",local_before,re.I)) or bool(re.match(r"\s*(?:при|за)\s*акт[^.!?]{0,16}\d+\s*%",local_after,re.I))
            if future_before or future_after or dated_future or deadline or payment or neg:
                rejected.append(f"Excluded as future/unachieved: {sn}")
                if neg: negatives.add(stage)
                continue
            candidates.append((stage,sn))
    attained={stage for stage,_ in candidates}
    if attained & negatives:
        both=sorted(attained & negatives,key=STAGES.index)
        return "conflict", [f"Conflicting attained and denied claims for {st}." for st in both] + [sn for st,sn in candidates if st in both][:4]
    if not candidates:
        return "unknown", rejected or ["No explicit attained construction-stage statement found in title/description."]
    chosen=max(attained,key=STAGES.index)
    evidence=[f"Attained {chosen}: {sn}" for st,sn in candidates if st==chosen][:5]
    lower=attained-{chosen}
    if lower: evidence.append("Earlier attained stage mentions are consistent with progression: "+", ".join(sorted(lower,key=STAGES.index)))
    return chosen, rejected[:4]+evidence

FURN_MARKERS = [
    ("furnished", re.compile(r"(?<!не)(?<!полу)(?:обзаведен(?:а|о|и)?|напълно\s+обзавед|луксозно\s+обзавед|мебелиран)|не\s+е\s+обзаведен(?:а|о|и)?|с\s+мебели(?:те)?|мебелите\s+са\s+включени", re.I)),
    ("unfurnished", re.compile(r"необзаведен(?:а|о|и)?|не\s+е\s+обзаведен(?:а|о|и)?|не\s+се\s+продава.{0,15}обзаведен|без\s+обзавеждане|без\s+мебел|празен\s+апартамент", re.I)),
    ("partial", re.compile(r"частично\s+обзавед|полуобзаведен(?:а|о|и)?|не\s+е\s+напълно\s+обзавед|кухня\s+с\s+уреди|вградени\s+(?:кухненски\s+)?уреди|обзаведен[аио]?\s+(?:само\s+)?(?:кухн|спалн)|с\s+кухненск[аио]?\s+обзавеждане", re.I)),
]

def classify_furnishing(title: str, desc: str) -> tuple[str,list[str]]:
    text=f"{title}\n{desc}"
    found=[]; evidence=[]
    for label,pat in FURN_MARKERS:
        for m in pat.finditer(text):
            ctx=_near(text,m.start(),m.end(),55); sn=_snip(text,m.start(),m.end(),65)
            # Ignore hypothetical offers and negated adjective fragments.
            furnishing_prefix=text[max(0,m.start()-55):m.start()]
            if re.search(r"(?:визуализац|илюстратив|генериран.{0,20}изображен|AI.{0,20}изображен)",ctx,re.I) and re.search(r"обзаведен\s+вид|изображен",ctx,re.I):
                evidence.append(f"Excluded rendered furnishing reference: {sn}"); continue
            if label in {"furnished","partial"} and re.search(r"(?:кът\s+за\s+отдих|общи\s+части|срещи\s+с\s+камин|лобби)",ctx,re.I) and not re.search(r"(?:апартамент|имот|жилищ).{0,35}обзавед|обзавед.{0,35}(?:апартамент|имот|жилищ)",ctx,re.I):
                evidence.append(f"Excluded shared-area furnishing: {sn}"); continue
            if re.search(r"може\s+да\s+(?:бъде|се\s+закупи)|ще\s+бъде|възможност|по\s+желание|да\s+се",furnishing_prefix,re.I) and not re.search(r"[.!?][^.!?]*$",furnishing_prefix):
                evidence.append(f"Excluded hypothetical furnishing: {sn}"); continue
            if label=="furnished" and (re.search(r"не\s+(?:е\s+)?(?:напълно\s+)?обзавед|не\s+се\s+продава.{0,15}обзавед|без\s+обзавеждане",ctx,re.I) or re.search(r"частично\s*$",furnishing_prefix,re.I) or re.search(r"не\s+е\s+напълно\s*$",furnishing_prefix,re.I)):
                continue
            found.append((label,sn))
    labels={x for x,_ in found}
    if not labels:
        return "unknown", evidence or ["No explicit furnishing-status statement found in title/description."]
    if "unfurnished" in labels and "furnished" in labels:
        if re.search(r"(?:само\s+.{0,20}не\s+е\s+обзавед|необзаведен[аио]?\s+(?:спалн|стая|хол|кухн)|не\s+е\s+обзаведен[аио]?\s+(?:спалн|стая|хол|кухн))",text,re.I):
            return "partial", [f"partial: mixed room-level furnishing: {sn}" for _,sn in found[:6]]
        return "conflict", [f"Conflicting furnishing claims: {sn}" for _,sn in found[:6]]
    if "unfurnished" in labels: chosen="unfurnished"
    elif "furnished" in labels: chosen="furnished"
    elif "partial" in labels: chosen="partial"
    else: chosen="furnished"
    return chosen,[f"{chosen}: {sn}" for label,sn in found if label==chosen][:6] or evidence

def classify_record(record: dict) -> dict:
    listing=record.get("listing") or {}
    title=str(listing.get("title") or "")
    desc=str(listing.get("description") or "")
    stage,se=classify_stage(title,desc,listing)
    furnishing,fe=classify_furnishing(title,desc)
    return {"provider":record.get("provider"),"originalUrl":listing.get("originalUrl"),"stage":stage,"furnishing":furnishing,
            "stageEvidence":se,"furnishingEvidence":fe,"method":"bg-property-stage-furnishing-rules-v2"}

def run(source: Path, outdir: Path) -> dict:
    raw=source.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    stage_counts=Counter(); furn_counts=Counter(); n=0
    outdir.mkdir(parents=True,exist_ok=True)
    target=outdir/"listing-classifications.jsonl"
    csv_target=outdir/"listing-classifications.csv"
    summary_target=outdir/"summary.json"
    jsonl_tmp=target.with_suffix(target.suffix+".tmp")
    csv_tmp=csv_target.with_suffix(csv_target.suffix+".tmp")
    summary_tmp=summary_target.with_suffix(summary_target.suffix+".tmp")
    with source.open(encoding="utf-8") as inp, jsonl_tmp.open("w",encoding="utf-8") as out, csv_tmp.open("w",encoding="utf-8-sig",newline="") as csv_file:
        csv_writer=csv.DictWriter(csv_file,fieldnames=["provider","originalUrl","stage","furnishing","stageEvidence","furnishingEvidence","method"])
        csv_writer.writeheader()
        for line_no,line in enumerate(inp,1):
            if not line.strip(): continue
            try: record=json.loads(line)
            except json.JSONDecodeError as e: raise ValueError(f"Invalid JSON on line {line_no}: {e}") from e
            result=classify_record(record); out.write(json.dumps(result,ensure_ascii=False)+"\n")
            csv_row=dict(result)
            csv_row["stageEvidence"]=json.dumps(result["stageEvidence"],ensure_ascii=False)
            csv_row["furnishingEvidence"]=json.dumps(result["furnishingEvidence"],ensure_ascii=False)
            csv_writer.writerow(csv_row)
            n+=1; stage_counts[result["stage"]]+=1; furn_counts[result["furnishing"]]+=1
    summary={"method":"Deterministic Bulgarian text rules; full title and description; no per-record LLM or human verification.",
             "methodVersion":"bg-property-stage-furnishing-rules-v2","sourcePath":str(source),"sourceSha256":digest,
             "sourceDate":"2026-10-22","recordCount":n,"stageCounts":dict(sorted(stage_counts.items())),
             "furnishingCounts":dict(sorted(furn_counts.items())),"classificationPath":str(target),"classificationCsvPath":str(csv_target)}
    summary_tmp.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    # Build every artifact completely first, then atomically replace each published path.
    os.replace(jsonl_tmp,target)
    os.replace(csv_tmp,csv_target)
    os.replace(summary_tmp,summary_target)
    return summary

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("source",type=Path); ap.add_argument("--outdir",type=Path,default=Path("classifications")); args=ap.parse_args()
    print(json.dumps(run(args.source,args.outdir),ensure_ascii=False,indent=2))
