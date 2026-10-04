import type { useTranslations } from "next-intl";

type EncountersTranslator = ReturnType<typeof useTranslations<"encounters">>;

export function templateFieldLabel(
  t: EncountersTranslator,
  labelKey: string,
): string {
  const key = labelKey.startsWith("encounters.")
    ? labelKey.slice("encounters.".length)
    : labelKey;
  switch (key) {
    case "templates.ear_pain.fields.associated_discharge":
      return t("templates.ear_pain.fields.associated_discharge");
    case "templates.ear_pain.fields.radiation_to_jaw":
      return t("templates.ear_pain.fields.radiation_to_jaw");
    case "templates.ear_pain.fields.swimming_exposure":
      return t("templates.ear_pain.fields.swimming_exposure");
    case "templates.ear_pain.name":
      return t("templates.ear_pain.name");
    case "templates.epistaxis.fields.anticoagulant_use":
      return t("templates.epistaxis.fields.anticoagulant_use");
    case "templates.epistaxis.fields.frequency":
      return t("templates.epistaxis.fields.frequency");
    case "templates.epistaxis.fields.hypertension_history":
      return t("templates.epistaxis.fields.hypertension_history");
    case "templates.epistaxis.name":
      return t("templates.epistaxis.name");
    case "templates.facial_pain.fields.bending_forward_worse":
      return t("templates.facial_pain.fields.bending_forward_worse");
    case "templates.facial_pain.fields.dental_symptoms":
      return t("templates.facial_pain.fields.dental_symptoms");
    case "templates.facial_pain.fields.sinus_distribution":
      return t("templates.facial_pain.fields.sinus_distribution");
    case "templates.facial_pain.name":
      return t("templates.facial_pain.name");
    case "templates.hearing_loss.fields.family_history":
      return t("templates.hearing_loss.fields.family_history");
    case "templates.hearing_loss.fields.noise_exposure":
      return t("templates.hearing_loss.fields.noise_exposure");
    case "templates.hearing_loss.fields.onset_profile":
      return t("templates.hearing_loss.fields.onset_profile");
    case "templates.hearing_loss.fields.ototoxic_medications":
      return t("templates.hearing_loss.fields.ototoxic_medications");
    case "templates.hearing_loss.name":
      return t("templates.hearing_loss.name");
    case "templates.hoarseness.fields.duration_weeks":
      return t("templates.hoarseness.fields.duration_weeks");
    case "templates.hoarseness.fields.dysphagia_or_weight_loss":
      return t("templates.hoarseness.fields.dysphagia_or_weight_loss");
    case "templates.hoarseness.fields.professional_voice_user":
      return t("templates.hoarseness.fields.professional_voice_user");
    case "templates.hoarseness.fields.smoking_history":
      return t("templates.hoarseness.fields.smoking_history");
    case "templates.hoarseness.name":
      return t("templates.hoarseness.name");
    case "templates.nasal_obstruction.fields.facial_pressure":
      return t("templates.nasal_obstruction.fields.facial_pressure");
    case "templates.nasal_obstruction.fields.hyposmia":
      return t("templates.nasal_obstruction.fields.hyposmia");
    case "templates.nasal_obstruction.fields.mouth_breathing":
      return t("templates.nasal_obstruction.fields.mouth_breathing");
    case "templates.nasal_obstruction.fields.pattern":
      return t("templates.nasal_obstruction.fields.pattern");
    case "templates.nasal_obstruction.fields.spray_overuse":
      return t("templates.nasal_obstruction.fields.spray_overuse");
    case "templates.nasal_obstruction.fields.worse_lying_down":
      return t("templates.nasal_obstruction.fields.worse_lying_down");
    case "templates.nasal_obstruction.name":
      return t("templates.nasal_obstruction.name");
    case "templates.rhinorrhea.fields.discharge_character":
      return t("templates.rhinorrhea.fields.discharge_character");
    case "templates.rhinorrhea.fields.itchy_eyes_palate":
      return t("templates.rhinorrhea.fields.itchy_eyes_palate");
    case "templates.rhinorrhea.fields.seasonality":
      return t("templates.rhinorrhea.fields.seasonality");
    case "templates.rhinorrhea.fields.sneezing_paroxysms":
      return t("templates.rhinorrhea.fields.sneezing_paroxysms");
    case "templates.rhinorrhea.name":
      return t("templates.rhinorrhea.name");
    case "templates.sore_throat.fields.antibiotic_courses":
      return t("templates.sore_throat.fields.antibiotic_courses");
    case "templates.sore_throat.fields.episodes_past_12m":
      return t("templates.sore_throat.fields.episodes_past_12m");
    case "templates.sore_throat.fields.peritonsillar_abscess_history":
      return t("templates.sore_throat.fields.peritonsillar_abscess_history");
    case "templates.sore_throat.name":
      return t("templates.sore_throat.name");
    case "templates.tinnitus.fields.pitch_character":
      return t("templates.tinnitus.fields.pitch_character");
    case "templates.tinnitus.fields.pulsatile":
      return t("templates.tinnitus.fields.pulsatile");
    case "templates.tinnitus.fields.sleep_interference":
      return t("templates.tinnitus.fields.sleep_interference");
    case "templates.tinnitus.name":
      return t("templates.tinnitus.name");
    case "templates.vertigo.fields.auditory_symptoms":
      return t("templates.vertigo.fields.auditory_symptoms");
    case "templates.vertigo.fields.migraine_history":
      return t("templates.vertigo.fields.migraine_history");
    case "templates.vertigo.fields.neurological_red_flags":
      return t("templates.vertigo.fields.neurological_red_flags");
    case "templates.vertigo.fields.timing_and_triggers":
      return t("templates.vertigo.fields.timing_and_triggers");
    case "templates.vertigo.name":
      return t("templates.vertigo.name");
    default:
      return t("history.fieldUnavailable");
  }
}

export function templateOptionLabel(
  t: EncountersTranslator,
  fieldId: string,
  option: string,
): string {
  switch (`${fieldId}.${option}`) {
    case "discharge_character.blood_stained":
      return t(
        "templates.rhinorrhea.fields.discharge_character_options.blood_stained",
      );
    case "discharge_character.clear_watery":
      return t(
        "templates.rhinorrhea.fields.discharge_character_options.clear_watery",
      );
    case "discharge_character.mucoid":
      return t(
        "templates.rhinorrhea.fields.discharge_character_options.mucoid",
      );
    case "discharge_character.purulent":
      return t(
        "templates.rhinorrhea.fields.discharge_character_options.purulent",
      );
    case "frequency.isolated":
      return t("templates.epistaxis.fields.frequency_options.isolated");
    case "frequency.recurrent_daily":
      return t("templates.epistaxis.fields.frequency_options.recurrent_daily");
    case "frequency.recurrent_weekly":
      return t("templates.epistaxis.fields.frequency_options.recurrent_weekly");
    case "onset_profile.fluctuating":
      return t(
        "templates.hearing_loss.fields.onset_profile_options.fluctuating",
      );
    case "onset_profile.progressive":
      return t(
        "templates.hearing_loss.fields.onset_profile_options.progressive",
      );
    case "onset_profile.sudden":
      return t("templates.hearing_loss.fields.onset_profile_options.sudden");
    case "pattern.alternating":
      return t(
        "templates.nasal_obstruction.fields.pattern_options.alternating",
      );
    case "pattern.constant":
      return t("templates.nasal_obstruction.fields.pattern_options.constant");
    case "pitch_character.clicking":
      return t("templates.tinnitus.fields.pitch_character_options.clicking");
    case "pitch_character.high_pitched":
      return t(
        "templates.tinnitus.fields.pitch_character_options.high_pitched",
      );
    case "pitch_character.low_hum":
      return t("templates.tinnitus.fields.pitch_character_options.low_hum");
    case "pitch_character.white_noise":
      return t("templates.tinnitus.fields.pitch_character_options.white_noise");
    case "seasonality.autumn":
      return t("templates.rhinorrhea.fields.seasonality_options.autumn");
    case "seasonality.perennial":
      return t("templates.rhinorrhea.fields.seasonality_options.perennial");
    case "seasonality.spring":
      return t("templates.rhinorrhea.fields.seasonality_options.spring");
    case "seasonality.summer":
      return t("templates.rhinorrhea.fields.seasonality_options.summer");
    case "sinus_distribution.diffuse":
      return t(
        "templates.facial_pain.fields.sinus_distribution_options.diffuse",
      );
    case "sinus_distribution.ethmoid":
      return t(
        "templates.facial_pain.fields.sinus_distribution_options.ethmoid",
      );
    case "sinus_distribution.frontal":
      return t(
        "templates.facial_pain.fields.sinus_distribution_options.frontal",
      );
    case "sinus_distribution.maxillary":
      return t(
        "templates.facial_pain.fields.sinus_distribution_options.maxillary",
      );
    case "sinus_distribution.sphenoid":
      return t(
        "templates.facial_pain.fields.sinus_distribution_options.sphenoid",
      );
    case "timing_and_triggers.continuous_days":
      return t(
        "templates.vertigo.fields.timing_and_triggers_options.continuous_days",
      );
    case "timing_and_triggers.head_motion_induced":
      return t(
        "templates.vertigo.fields.timing_and_triggers_options.head_motion_induced",
      );
    case "timing_and_triggers.positional_seconds":
      return t(
        "templates.vertigo.fields.timing_and_triggers_options.positional_seconds",
      );
    case "timing_and_triggers.spontaneous_hours":
      return t(
        "templates.vertigo.fields.timing_and_triggers_options.spontaneous_hours",
      );
    default:
      return t("history.optionUnavailable");
  }
}
