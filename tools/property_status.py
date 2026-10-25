"""Buyer-facing combined status, without inferring a construction act from furniture."""
STATUS_LABELS = {
 'green': 'На зелено',
 'act14': 'Акт 14',
 'act15': 'Акт 15',
 'act16_furnished': 'Акт 16 + обзаведен',
 'act16_partial': 'Акт 16 + частично обзаведен',
 'act16_unfurnished': 'Акт 16 + необзаведен',
 'act16_unspecified': 'Акт 16 · обзавеждане неуточнено',
 'furnished_stage_unknown': 'Обзаведен · акт неуточнен',
 'unknown': 'Акт / етап неуточнен',
 'review': 'За проверка · несъответстващи твърдения',
 'not_applicable': 'Неприложимо (земя)',
}

def combined_status(stage, furnishing):
 if 'conflict' in (stage,furnishing): return 'review'
 if stage in ('green','act14','act15'):
  return 'review' if furnishing in ('furnished','partial') else stage
 if stage=='act16':
  return 'act16_'+({'furnished':'furnished','partial':'partial','unfurnished':'unfurnished'}.get(furnishing,'unspecified'))
 if stage=='not_applicable':return 'not_applicable'
 if furnishing=='furnished':return 'furnished_stage_unknown'
 return 'unknown'
