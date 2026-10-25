import unittest
from classify_properties import classify_stage, classify_furnishing

class ClassificationTests(unittest.TestCase):
    def stage(self, text):
        return classify_stage("Продава апартамент", text, {})[0]
    def furnishing(self, text):
        return classify_furnishing("Продава апартамент", text)[0]

    def test_attained_higher_stage_wins(self):
        self.assertEqual(self.stage("Сградата е с акт 14, има акт образец 15."), "act15")
    def test_future_act16_does_not_override_act14(self):
        self.assertEqual(self.stage("На акт 14, акт 16 се очаква през 2028 г."), "act14")
    def test_attained_act14_survives_future_commissioning(self):
        self.assertEqual(self.stage("Сградата е на етап АКТ 14, а въвеждане в експлоатация се очаква до края на 2027г."), "act14")
    def test_act14_survives_later_commissioning_planned_for_2027(self):
        self.assertEqual(self.stage("Сградата е със заверен Груб строеж (Акт 14), като въвеждането в експлоатация (Акт 16) е заложено за края на 2027г."), "act14")
    def test_act15_survives_predicted_future_commissioning(self):
        self.assertEqual(self.stage("Сградата е с Акт 15. Предвижда се сградата да бъде въведена в експлоатация до Нова година."), "act15")
    def test_listing_verb_does_not_look_like_pred_act(self):
        self.assertEqual(self.stage("Имотът се предлага на етап Акт 14, с издадено удостоверение по чл.181."), "act14")
    def test_future_finish_does_not_erase_attained_act14(self):
        self.assertEqual(self.stage("Къщата към днешна дата е с Акт 14 като ще бъде напълно завършена и обзаведена."), "act14")
    def test_act16_and_permit_synonym_share_future_date(self):
        self.assertEqual(self.stage("Етап на строителство: Акт 16 / Разрешение за ползване Пролет 2027г."), "unknown")
    def test_act16_with_historical_year_is_attained(self):
        self.assertEqual(self.stage("Сградата е с Акт 16 от 2008 г. и се предлага за продажба."), "act16")
    def test_act16_in_building_description_after_neposleden(self):
        self.assertEqual(self.stage("Тухлена монолитна сграда с акт 16 от 1997 г., отлично поддържана."), "act16")
    def test_historical_act16_is_not_cancelled_by_unrelated_future_year(self):
        self.assertEqual(self.stage("Сградата е с Акт 16 от 1997 г. Имотът може да бъде реновиран през 2028 г."), "act16")
    def test_pred_act_is_not_attained(self):
        self.assertEqual(self.stage("Сградата е пред акт 15."), "unknown")
    def test_future_act16_does_not_override_act15(self):
        self.assertEqual(self.stage("Етап: акт обр.15. Очакван Акт 16 в края на 2026 г."), "act15")
    def test_future_only_is_unknown(self):
        self.assertEqual(self.stage("Очакван Акт 16 през 2027 г."), "unknown")
    def test_later_milestone_year_is_not_attained(self):
        self.assertEqual(self.stage("Акт 16 през март 2027 г."), "unknown")
    def test_payment_schedule_is_not_attained_stage(self):
        self.assertEqual(self.stage("40% при Акт 14, 20% при Акт 15, 10% при Акт 16."), "unknown")
    def test_negative_act16_not_attained(self):
        self.assertEqual(self.stage("Без акт 16, сградата е с акт 14."), "act14")
    def test_latin_a_act_spelling(self):
        self.assertEqual(self.stage("С Aкт14, очакван акт16 декември 2027г."), "act14")
    def test_payment_or_after_act16_not_attained(self):
        self.assertEqual(self.stage("25% сега, останалото след АКТ16."), "unknown")
    def test_end_of_year_act16_is_pending(self):
        self.assertEqual(self.stage("Акт 16 до края на годината."), "unknown")
    def test_documents_filed_for_act_is_pending(self):
        self.assertEqual(self.stage("Подадени документи за Акт 14."), "unknown")
    def test_negation_in_next_sentence_does_not_apply(self):
        self.assertEqual(self.stage("Сграда с АКТ16. Без комисиона."), "act16")
    def test_commission_without_punctuation_does_not_negate_stage(self):
        self.assertEqual(classify_stage("", "Сграда с АКТ16 и без комисиона.", {})[0], "act16")
    def test_permit_to_use_means_act16(self):
        self.assertEqual(self.stage("Сградата е въведена в експлоатация."), "act16")
        self.assertEqual(self.stage("Очаква се разрешение за ползване през 2027 г."), "unknown")
    def test_attained_and_denied_same_stage_is_conflict(self):
        self.assertEqual(self.stage("Сградата има акт 16, но няма акт 16."), "conflict")
    def test_green_requires_explicit_phrase(self):
        self.assertEqual(self.stage("Проектът е на зелено строителство."), "green")
        self.assertEqual(self.stage("Построена през 2024 г."), "unknown")
    def test_land_is_not_applicable(self):
        self.assertEqual(classify_stage("Продава парцел", "УПИ за строеж", {})[0], "not_applicable")
    def test_furnished_future_hypothetical_is_unknown(self):
        self.assertEqual(self.furnishing("Възможност имотът да бъде обзаведен по избор."), "unknown")
    def test_unfurnished_negation(self):
        self.assertEqual(self.furnishing("Апартаментът е необзаведен."), "unfurnished")
    def test_unfurnished_phrase_negation(self):
        self.assertEqual(self.furnishing("Имотът не е обзаведен."), "unfurnished")
    def test_negation_of_fully_furnished_is_partial(self):
        self.assertEqual(self.furnishing("Не е напълно обзаведен."), "partial")
    def test_not_sold_furnished_is_unfurnished(self):
        self.assertEqual(self.furnishing("Не се продава обзаведен."), "unfurnished")
    def test_future_furnishing_is_unknown(self):
        self.assertEqual(self.furnishing("Ще бъде обзаведен."), "unknown")
    def test_separate_parking_possibility_does_not_hide_furnishing(self):
        self.assertEqual(self.furnishing("Има възможност за паркомясто. Напълно обзаведен."), "furnished")
    def test_optional_furnishing_does_not_conflict(self):
        self.assertEqual(self.furnishing("Необзаведен, но може да се закупи обзаведен."), "unfurnished")
    def test_furniture_claim(self):
        self.assertEqual(self.furnishing("Продава се с мебели."), "furnished")
    def test_kitchen_appliances_only_partial(self):
        self.assertEqual(self.furnishing("Само кухнята е с вградени уреди."), "partial")
    def test_full_furnishing_overrides_equipped_kitchen(self):
        self.assertEqual(self.furnishing("Напълно обзаведен апартамент с вградени кухненски уреди."), "furnished")
    def test_partial(self):
        self.assertEqual(self.furnishing("С вградени кухненски уреди."), "partial")
    def test_explicit_partially_furnished(self):
        self.assertEqual(self.furnishing("Частично обзаведен апартамент."), "partial")
    def test_semi_furnished_is_partial(self):
        self.assertEqual(self.furnishing("Полуобзаведен едностаен апартамент."), "partial")
    def test_rendered_image_is_not_actual_furnishing(self):
        self.assertEqual(self.furnishing("AI генерирани изображения представят имота в завършен и обзаведен вид."), "unknown")
    def test_common_lounge_furniture_is_not_unit_furnishing(self):
        self.assertEqual(self.furnishing("Напълно обзаведен кът за отдих и срещи с камина."), "unknown")
    def test_conflicting_furnishing(self):
        self.assertEqual(self.furnishing("Напълно обзаведен, но имотът е необзаведен."), "conflict")
    def test_room_level_mixed_furnishing_is_partial(self):
        self.assertEqual(self.furnishing("Обзаведен апартамент, две необзаведени спални."), "partial")

if __name__ == "__main__": unittest.main()
