"""Launch questionnaire instrument definitions for P5-02 (Appendix A)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from ent.seeds.instruments_option_labels import (
    option_values_for_scale,
    shared_option_translations,
)


@dataclass(frozen=True, slots=True)
class LaunchItemText:
    code: str
    position: int
    en: str
    fr: str
    ar: str
    subscale: str | None = None


@dataclass(frozen=True, slots=True)
class SeverityBandDef:
    code: str
    min_score: Decimal
    max_score: Decimal


@dataclass(frozen=True, slots=True)
class SubscaleDef:
    code: str
    item_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LaunchInstrumentSpec:
    code: str
    category: str
    respondent: str
    scoring_type: str
    min_score: int
    max_score: int
    mcid: Decimal | None
    license_note: str
    reference: str
    scale_key: str
    scale_multiplier: Decimal
    title_en: str
    title_fr: str
    title_ar: str
    items: tuple[LaunchItemText, ...]
    severity_bands: tuple[SeverityBandDef, ...] = ()
    subscales: tuple[SubscaleDef, ...] = ()
    version: str = "1.0.0"
    effective_from: date = date(2026, 1, 1)


def _band(code: str, min_s: int | str, max_s: int | str) -> SeverityBandDef:
    return SeverityBandDef(
        code=code,
        min_score=Decimal(str(min_s)),
        max_score=Decimal(str(max_s)),
    )


_SNOT22_ITEMS: tuple[LaunchItemText, ...] = (
    LaunchItemText(
        "q1",
        1,
        "The need to blow the nose",
        "Besoin de se moucher",
        "الحاجة للنفخ بالأنف",
        "rhinologic",
    ),
    LaunchItemText("q2", 2, "Sneezing", "Éternuements", "العطس", "rhinologic"),
    LaunchItemText(
        "q3", 3, "Runny nose", "Écoulement nasal", "سيلان الأنف", "rhinologic"
    ),
    LaunchItemText(
        "q4", 4, "Nasal blockage", "Obstruction nasale", "انسداد الأنف", "rhinologic"
    ),
    LaunchItemText(
        "q5",
        5,
        "Loss of smell or taste",
        "Perte d'odorat ou de goût",
        "فقدان الشم أو التذوق",
        "rhinologic",
    ),
    LaunchItemText("q6", 6, "Cough", "Toux", "سعال", "extranasal"),
    LaunchItemText(
        "q7",
        7,
        "Post-nasal discharge",
        "Rhinorrhée postérieure",
        "إفرازات أنفية خلفية",
        "extranasal",
    ),
    LaunchItemText(
        "q8",
        8,
        "Thick nasal discharge",
        "Écoulement nasal épais",
        "إفرازات أنفية كثيفة",
        "extranasal",
    ),
    LaunchItemText(
        "q9", 9, "Ear fullness", "Plénitude auriculaire", "امتلاء الأذن", "ear_facial"
    ),
    LaunchItemText("q10", 10, "Dizziness", "Vertiges", "دوار", "ear_facial"),
    LaunchItemText(
        "q11", 11, "Ear pain", "Douleur auriculaire", "ألم الأذن", "ear_facial"
    ),
    LaunchItemText(
        "q12",
        12,
        "Facial pain or pressure",
        "Douleur ou pression faciale",
        "ألم أو ضغط في الوجه",
        "ear_facial",
    ),
    LaunchItemText(
        "q13",
        13,
        "Difficulty falling asleep",
        "Difficulté à s'endormir",
        "صعوبة النوم",
        "sleep",
    ),
    LaunchItemText(
        "q14", 14, "Wake up at night", "Réveils nocturnes", "الاستيقاظ ليلاً", "sleep"
    ),
    LaunchItemText(
        "q15",
        15,
        "Lack of a good night's sleep",
        "Sommeil non réparateur",
        "نوم غير مريح",
        "sleep",
    ),
    LaunchItemText(
        "q16", 16, "Wake up tired", "Réveil fatigué", "الاستيقاظ متعباً", "sleep"
    ),
    LaunchItemText("q17", 17, "Fatigue", "Fatigue", "إرهاق", "psychological"),
    LaunchItemText(
        "q18",
        18,
        "Reduced productivity",
        "Productivité réduite",
        "انخفاض الإنتاجية",
        "psychological",
    ),
    LaunchItemText(
        "q19",
        19,
        "Reduced concentration",
        "Concentration réduite",
        "صعوبة التركيز",
        "psychological",
    ),
    LaunchItemText(
        "q20",
        20,
        "Frustrated, restless, or irritable",
        "Frustration, agitation ou irritabilité",
        "إحباط أو هيجان أو تهيج",
        "psychological",
    ),
    LaunchItemText("q21", 21, "Sad", "Tristesse", "حزن", "psychological"),
    LaunchItemText(
        "q22", 22, "Embarrassed", "Gêne ou embarras", "إحراج", "psychological"
    ),
)

_NOSE_ITEMS: tuple[LaunchItemText, ...] = (
    LaunchItemText(
        "n1",
        1,
        "Nasal congestion or stuffiness",
        "Congestion ou obstruction nasale",
        "احتقان أو انسداد الأنف",
    ),
    LaunchItemText(
        "n2", 2, "Nasal blockage or obstruction", "Blocage nasal", "انسداد الأنف"
    ),
    LaunchItemText(
        "n3",
        3,
        "Trouble breathing through my nose",
        "Difficulté à respirer par le nez",
        "صعوبة التنفس عبر الأنف",
    ),
    LaunchItemText("n4", 4, "Trouble sleeping", "Troubles du sommeil", "اضطراب النوم"),
    LaunchItemText(
        "n5",
        5,
        "Unable to get enough air through my nose during exercise or exertion",
        "Air insuffisant par le nez à l'effort",
        "عدم كفاية الهواء عبر الأنف عند المجهود",
    ),
)

_THI_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(
        f"t{i}",
        i,
        en,
        fr,
        ar,
        sub,
    )
    for i, en, fr, ar, sub in (
        (
            1,
            "Because of my tinnitus, it is difficult to concentrate",
            "Difficulté à me concentrer à cause des acouphènes",
            "صعوبة التركيز بسبب الطنين",
            "functional",
        ),
        (
            2,
            "Because of my tinnitus, it is difficult to relax",
            "Difficulté à me détendre à cause des acouphènes",
            "صعوبة الاسترخاء بسبب الطنين",
            "functional",
        ),
        (
            3,
            "Because of my tinnitus, I feel irritated",
            "Irritation à cause des acouphènes",
            "التهيج بسبب الطنين",
            "emotional",
        ),
        (
            4,
            "Because of my tinnitus, I have difficulty focusing attention on reading",
            "Difficulté à lire à cause des acouphènes",
            "صعوبة القراءة بسبب الطنين",
            "functional",
        ),
        (
            5,
            "Because of my tinnitus, I have difficulty falling asleep",
            "Difficulté à m'endormir à cause des acouphènes",
            "صعوبة النوم بسبب الطنين",
            "catastrophic",
        ),
        (
            6,
            "Because of my tinnitus, I feel frustrated",
            "Frustration à cause des acouphènes",
            "إحباط بسبب الطنين",
            "emotional",
        ),
        (
            7,
            "Because of my tinnitus, I feel angry",
            "Colère à cause des acouphènes",
            "غضب بسبب الطنين",
            "emotional",
        ),
        (
            8,
            "Because of my tinnitus, I feel confused",
            "Confusion à cause des acouphènes",
            "ارتباك بسبب الطنين",
            "catastrophic",
        ),
        (
            9,
            "Because of my tinnitus, I feel depressed",
            "Dépression à cause des acouphènes",
            "اكتئاب بسبب الطنين",
            "emotional",
        ),
        (
            10,
            "Because of my tinnitus, I feel anxious",
            "Anxiété à cause des acouphènes",
            "قلق بسبب الطنين",
            "emotional",
        ),
        (
            11,
            "Because of my tinnitus, I feel helpless",
            "Impuissance à cause des acouphènes",
            "عجز بسبب الطنين",
            "catastrophic",
        ),
        (
            12,
            "Because of my tinnitus, I am stressed",
            "Stress à cause des acouphènes",
            "توتر بسبب الطنين",
            "functional",
        ),
        (
            13,
            "Because of my tinnitus, I feel irritated with family and friends",
            "Irritation envers l'entourage à cause des acouphènes",
            "التهيج من الأقارب بسبب الطنين",
            "functional",
        ),
        (
            14,
            "Because of my tinnitus, I have difficulty listening to the television or radio",
            "Difficulté à écouter la télévision ou la radio à cause des acouphènes",
            "صعوبة مشاهدة التلفاز أو الراديو بسبب الطنين",
            "emotional",
        ),
        (
            15,
            "Because of my tinnitus, I have difficulty listening to others speak",
            "Difficulté à écouter autrui à cause des acouphènes",
            "صعوبة سماع الكلام بسبب الطنين",
            "functional",
        ),
        (
            16,
            "Because of my tinnitus, I feel as though I cannot understand what others are saying",
            "Impression de ne pas comprendre autrui à cause des acouphènes",
            "شعور بعدم فهم الكلام بسبب الطنين",
            "emotional",
        ),
        (
            17,
            "Because of my tinnitus, I feel isolated",
            "Isolement à cause des acouphènes",
            "عزلة بسبب الطنين",
            "emotional",
        ),
        (
            18,
            "Because of my tinnitus, I have difficulty maintaining relationships",
            "Difficulté à maintenir des relations à cause des acouphènes",
            "صعوبة العلاقات بسبب الطنين",
            "functional",
        ),
        (
            19,
            "Because of my tinnitus, I feel lonely",
            "Solitude à cause des acouphènes",
            "وحدة بسبب الطنين",
            "catastrophic",
        ),
        (
            20,
            "Because of my tinnitus, it is difficult to enjoy life",
            "Difficulté à profiter de la vie à cause des acouphènes",
            "صعوبة الاستمتاع بالحياة بسبب الطنين",
            "functional",
        ),
        (
            21,
            "Because of my tinnitus, I have trouble coping with life",
            "Difficulté à faire face à la vie à cause des acouphènes",
            "صعوبة مواجهة الحياة بسبب الطنين",
            "emotional",
        ),
        (
            22,
            "Because of my tinnitus, I have difficulty earning a living",
            "Difficulté à travailler à cause des acouphènes",
            "صعوبة العمل بسبب الطنين",
            "emotional",
        ),
        (
            23,
            "Because of my tinnitus, I feel that I cannot escape from it",
            "Impression de ne pouvoir échapper aux acouphènes",
            "شعور بعدم القدرة على الهروب من الطنين",
            "catastrophic",
        ),
        (
            24,
            "Because of my tinnitus, I believe the noise will never go away",
            "Croyance que le bruit ne disparaîtra jamais",
            "اعتقاد أن الضوضاء لن تزول أبداً",
            "functional",
        ),
        (
            25,
            "Because of my tinnitus, I feel as though I have lost control",
            "Perte de contrôle à cause des acouphènes",
            "فقدان السيطرة بسبب الطنين",
            "emotional",
        ),
    )
)

_DHI_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"d{i}", i, en, fr, ar, sub)
    for i, en, fr, ar, sub in (
        (
            1,
            "Does looking up increase your dizziness?",
            "Regarder vers le haut augmente-t-il les vertiges ?",
            "هل النظر للأعلى يزيد الدوار؟",
            "physical",
        ),
        (
            2,
            "Because of your dizziness, do you feel frustrated?",
            "Les vertiges vous rendent-ils frustré ?",
            "هل تشعر بالإحباط بسبب الدوار؟",
            "emotional",
        ),
        (
            3,
            "Because of your dizziness, do you restrict your travel?",
            "Limitez-vous vos déplacements à cause des vertiges ?",
            "هل تقيد السفر بسبب الدوار؟",
            "functional",
        ),
        (
            4,
            "Does walking down the aisle of a supermarket increase your dizziness?",
            "Marcher dans une allée de supermarché augmente-t-il les vertiges ?",
            "هل المشي في ممر متجر يزيد الدوار؟",
            "physical",
        ),
        (
            5,
            "Because of your dizziness, do you avoid heights?",
            "Évitez-vous les hauteurs à cause des vertiges ?",
            "هل تتجنب المرتفعات بسبب الدوار؟",
            "functional",
        ),
        (
            6,
            "Does bending over increase your dizziness?",
            "Se pencher augmente-t-il les vertiges ?",
            "هل الانحناء يزيد الدوار؟",
            "physical",
        ),
        (
            7,
            "Because of your dizziness, do you avoid leaving your home?",
            "Évitez-vous de quitter votre domicile à cause des vertiges ?",
            "هل تتجنب مغادرة المنزل بسبب الدوار؟",
            "functional",
        ),
        (
            8,
            "Does quickly turning your head increase your dizziness?",
            "Tourner rapidement la tête augmente-t-il les vertiges ?",
            "هل لف الرأس بسرعة يزيد الدوار؟",
            "physical",
        ),
        (
            9,
            "Because of your dizziness, are you afraid people may think you are intoxicated?",
            "Craignez-vous qu'on pense que vous êtes ivre ?",
            "هل تخشى أن يظن الناس أنك ثمل بسبب الدوار؟",
            "emotional",
        ),
        (
            10,
            "Because of your dizziness, are you embarrassed?",
            "Les vertiges vous gênent-ils ?",
            "هل تشعر بالإحراج بسبب الدوار؟",
            "emotional",
        ),
        (
            11,
            "Do activities which require good balance increase your dizziness?",
            "Les activités demandant l'équilibre augmentent-elles les vertiges ?",
            "هل الأنشطة التي تتطلب التوازن تزيد الدوار؟",
            "physical",
        ),
        (
            12,
            "Because of your dizziness, do you avoid walking by yourself?",
            "Évitez-vous de marcher seul à cause des vertiges ?",
            "هل تتجنب المشي وحيداً بسبب الدوار؟",
            "functional",
        ),
        (
            13,
            "Does walking down a sidewalk increase your dizziness?",
            "Marcher sur le trottoir augmente-t-il les vertiges ?",
            "هل المشي على الرصيف يزيد الدوار؟",
            "physical",
        ),
        (
            14,
            "Because of your dizziness, do you avoid sudden changes in head position?",
            "Évitez-vous les mouvements brusques de la tête ?",
            "هل تتجنب الحركات المفاجئة للرأس بسبب الدوار؟",
            "functional",
        ),
        (
            15,
            "Because of your dizziness, are you afraid to leave your home without help?",
            "Avez-vous peur de sortir sans aide à cause des vertiges ?",
            "هل تخاف المغادرة دون مساعدة بسبب الدوار؟",
            "emotional",
        ),
        (
            16,
            "Because of your dizziness, do you avoid going out in the dark?",
            "Évitez-vous de sortir dans le noir ?",
            "هل تتجنب الخروج في الظلام بسبب الدوار؟",
            "functional",
        ),
        (
            17,
            "Because of your dizziness, are you afraid to stay home alone?",
            "Avez-vous peur de rester seul à cause des vertiges ?",
            "هل تخاف البقاء وحدك بسبب الدوار؟",
            "emotional",
        ),
        (
            18,
            "Because of your dizziness, do you feel handicapped?",
            "Vous sentez-vous handicapé par les vertiges ?",
            "هل تشعر بإعاقة بسبب الدوار؟",
            "emotional",
        ),
        (
            19,
            "Because of your dizziness, are you afraid people may think you are exaggerating?",
            "Craignez-vous qu'on pense que vous exagérez ?",
            "هل تخشى أن يظن الناس أنك مبالغ بسبب الدوار؟",
            "functional",
        ),
        (
            20,
            "Because of your dizziness, are you afraid to go out alone?",
            "Avez-vous peur de sortir seul ?",
            "هل تخاف الخروج وحدك بسبب الدوار؟",
            "emotional",
        ),
        (
            21,
            "Because of your dizziness, are you afraid to go out in crowds?",
            "Avez-vous peur des foules à cause des vertiges ?",
            "هل تخاف الحشود بسبب الدوار؟",
            "emotional",
        ),
        (
            22,
            "Because of your dizziness, are you afraid to go out on busy streets?",
            "Avez-vous peur des rues animées ?",
            "هل تخاف الشوارع المزدحمة بسبب الدوار؟",
            "emotional",
        ),
        (
            23,
            "Because of your dizziness, are you afraid people may think you are lazy?",
            "Craignez-vous qu'on pense que vous êtes paresseux ?",
            "هل تخشى أن يظن الناس أنك كسول بسبب الدوار؟",
            "emotional",
        ),
        (
            24,
            "Because of your dizziness, are you afraid people may think you are mentally ill?",
            "Craignez-vous qu'on pense que vous êtes malade mentalement ?",
            "هل تخشى أن يظن الناس أنك مريض نفسياً بسبب الدوار؟",
            "functional",
        ),
        (
            25,
            "Because of your dizziness, are you afraid to go up on escalators?",
            "Avez-vous peur des escalators ?",
            "هل تخاف السلالم المتحركة بسبب الدوار؟",
            "physical",
        ),
    )
)

_VHI10_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"v{i}", i, en, fr, ar, sub)
    for i, en, fr, ar, sub in (
        (
            1,
            "My voice makes it difficult for people to hear me",
            "Ma voix rend difficile de m'entendre",
            "صوتي يصعّب على الناس سماعي",
            "functional",
        ),
        (
            2,
            "I run out of air when I talk",
            "Je manque d'air en parlant",
            "ينفد هوائي عند الكلام",
            "physical",
        ),
        (
            3,
            "People have difficulty understanding me in a noisy room",
            "On a du mal à me comprendre dans le bruit",
            "صعوبة فهمي في مكان صاخب",
            "functional",
        ),
        (
            4,
            "The sound of my voice varies throughout the day",
            "Le son de ma voix varie dans la journée",
            "صوتي يتغير خلال اليوم",
            "physical",
        ),
        (
            5,
            "My family has difficulty hearing me when I call them",
            "Ma famille a du mal à m'entendre à la maison",
            "عائلتي لا تسمعني عندما أنادي",
            "functional",
        ),
        (
            6,
            "I use the phone less often than I would like",
            "J'utilise moins le téléphone que je le souhaiterais",
            "أستخدم الهاتف أقل مما أريد",
            "functional",
        ),
        (
            7,
            "I am tense when talking to others because of my voice",
            "Je suis tendu en parlant à cause de ma voix",
            "أشعر بالتوتر عند الكلام بسبب صوتي",
            "emotional",
        ),
        (
            8,
            "I tend to avoid groups of people because of my voice",
            "J'évite les groupes à cause de ma voix",
            "أتجنب التجمعات بسبب صوتي",
            "functional",
        ),
        (
            9,
            "People seem irritated with my voice",
            "Les gens semblent irrités par ma voix",
            "يبدو أن الناس منزعجين من صوتي",
            "emotional",
        ),
        (
            10,
            "People ask what is wrong with my voice",
            "On me demande ce qui ne va pas avec ma voix",
            "يسألونني ما الخطأ في صوتي",
            "physical",
        ),
    )
)

_RSI_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"r{i}", i, en, fr, ar)
    for i, en, fr, ar in (
        (
            1,
            "Hoarseness or a problem with your voice",
            "Enrouement ou trouble de la voix",
            "بحة أو مشكلة في الصوت",
        ),
        (2, "Clearing your throat", "Besoin de s'éclaircir la gorge", "تنظيف الحلق"),
        (
            3,
            "Excess throat mucus or postnasal drip",
            "Mucus excessif ou écoulement postérieur",
            "مخاط حلقي زائد أو إفرازات خلفية",
        ),
        (
            4,
            "Difficulty swallowing food, liquids, or pills",
            "Difficulté à avaler nourriture, liquides ou comprimés",
            "صعوبة بلع الطعام أو السوائل أو الحبوب",
        ),
        (
            5,
            "Coughing after you ate or after lying down",
            "Toux après manger ou en position couchée",
            "سعال بعد الأكل أو عند الاستلقاء",
        ),
        (
            6,
            "Breathing difficulties or choking episodes",
            "Difficultés respiratoires ou étouffements",
            "صعوبة تنفس أو اختناق",
        ),
        (7, "Troublesome or annoying cough", "Toux gênante ou importune", "سعال مزعج"),
        (
            8,
            "Sensations of something sticking in your throat",
            "Sensation de corps étranger dans la gorge",
            "إحساس بشيء عالق في الحلق",
        ),
        (
            9,
            "Heartburn, chest pain, indigestion, or stomach acid coming up",
            "Brûlures, douleur thoracique, indigestion ou reflux",
            "حموضة أو ألم صدري أو عسر هضم أو ارتجاع",
        ),
    )
)

_EAT10_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"e{i}", i, en, fr, ar)
    for i, en, fr, ar in (
        (
            1,
            "My swallowing problem has caused me to lose weight",
            "Mes troubles de déglutition m'ont fait perdre du poids",
            "مشكلة البلع أدت لفقدان الوزن",
        ),
        (
            2,
            "My swallowing problem interferes with my ability to go out for meals",
            "Mes troubles de déglutition gênent mes repas à l'extérieur",
            "مشكلة البلع تعيق الخروج لتناول الطعام",
        ),
        (
            3,
            "Swallowing liquids takes extra effort",
            "Avaler les liquides demande un effort supplémentaire",
            "بلع السوائل يحتاج جهداً إضافياً",
        ),
        (
            4,
            "Swallowing solids takes extra effort",
            "Avaler les solides demande un effort supplémentaire",
            "بلع الصلب يحتاج جهداً إضافياً",
        ),
        (
            5,
            "Swallowing pills takes extra effort",
            "Avaler les comprimés demande un effort supplémentaire",
            "بلع الحبوب يحتاج جهداً إضافياً",
        ),
        (6, "Swallowing is painful", "La déglutition est douloureuse", "البلع مؤلم"),
        (
            7,
            "The pleasure of eating is affected by my swallowing",
            "Le plaisir de manger est affecté par ma déglutition",
            "متعة الأكل متأثرة بمشكلة البلع",
        ),
        (
            8,
            "When I swallow food sticks in my throat",
            "La nourriture reste coincée dans ma gorge",
            "الطعام يعلق في حلقي عند البلع",
        ),
        (9, "I cough when I eat", "Je tousse en mangeant", "أسعل عند الأكل"),
        (
            10,
            "Swallowing is stressful",
            "La déglutition est stressante",
            "البلع مسبب للتوتر",
        ),
    )
)

_EPWORTH_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"ep{i}", i, en, fr, ar)
    for i, en, fr, ar in (
        (1, "Sitting and reading", "Assis et en train de lire", "الجلوس والقراءة"),
        (2, "Watching TV", "Regarder la télévision", "مشاهدة التلفاز"),
        (
            3,
            "Sitting inactive in a public place",
            "Assis inactif dans un lieu public",
            "الجلوس بلا نشاط في مكان عام",
        ),
        (
            4,
            "As a passenger in a car for an hour without a break",
            "Passager en voiture pendant une heure sans pause",
            "راكب سيارة ساعة دون توقف",
        ),
        (
            5,
            "Lying down to rest in the afternoon when possible",
            "S'allonger l'après-midi pour se reposer",
            "الاستلقاء بعد الظهر للراحة",
        ),
        (
            6,
            "Sitting and talking to someone",
            "Assis en conversation",
            "الجلوس والتحدث مع أحد",
        ),
        (
            7,
            "Sitting quietly after lunch without alcohol",
            "Assis calmement après le déjeuner sans alcool",
            "الجلوس بهدوء بعد الغداء دون كحول",
        ),
        (
            8,
            "In a car, stopped for a few minutes in traffic",
            "En voiture, arrêté quelques minutes dans les embouteillages",
            "في سيارة متوقفة دقائق في ازدحام",
        ),
    )
)

_STOPBANG_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"sb{i}", i, en, fr, ar)
    for i, en, fr, ar in (
        (1, "Do you snore loudly?", "Ronflez-vous fort ?", "هل تشخر بصوت عالٍ؟"),
        (
            2,
            "Do you often feel tired, fatigued, or sleepy during daytime?",
            "Êtes-vous souvent fatigué ou somnolent le jour ?",
            "هل تشعر بالتعب أو النعاس نهاراً؟",
        ),
        (
            3,
            "Has anyone observed you stop breathing or choking during sleep?",
            "Quelqu'un a-t-il observé des pauses respiratoires ou des étouffements ?",
            "هل لاحظ أحد توقف تنفسك أو اختناقك أثناء النوم؟",
        ),
        (
            4,
            "Do you have or are you treated for high blood pressure?",
            "Avez-vous ou suivez-vous un traitement pour l'hypertension ?",
            "هل لديك أو تعالج من ارتفاع ضغط الدم؟",
        ),
        (
            5,
            "Is your body mass index more than 35 kg/m²?",
            "Votre IMC est-il supérieur à 35 kg/m² ?",
            "هل مؤشر كتلة جسمك أكثر من 35؟",
        ),
        (
            6,
            "Are you older than 50 years?",
            "Avez-vous plus de 50 ans ?",
            "هل عمرك أكثر من 50 سنة؟",
        ),
        (
            7,
            "Is your neck circumference greater than 40 cm?",
            "Votre tour de cou est-il supérieur à 40 cm ?",
            "هل محيط عنقك أكبر من 40 سم؟",
        ),
        (8, "Are you male?", "Êtes-vous de sexe masculin ?", "هل أنت ذكر؟"),
    )
)

_OSA18_ITEMS: tuple[LaunchItemText, ...] = tuple(
    LaunchItemText(f"osa{i}", i, en, fr, ar, sub)
    for i, en, fr, ar, sub in (
        (1, "Loud snoring", "Ronflement fort", "شخير عالٍ", "sleep_disturbance"),
        (
            2,
            "Breath holding or pauses",
            "Pauses respiratoires",
            "توقف التنفس",
            "sleep_disturbance",
        ),
        (
            3,
            "Choking or gasping",
            "Étouffements ou halètements",
            "اختناق أولهاث",
            "sleep_disturbance",
        ),
        (
            4,
            "Restless sleep or frequent awakenings",
            "Sommeil agité ou réveils fréquents",
            "نوم مضطرب أو استيقاظ متكرر",
            "sleep_disturbance",
        ),
        (
            5,
            "Mouth breathing because of nasal obstruction",
            "Respiration buccale par obstruction nasale",
            "تنفس فموي بسبب انسداد الأنف",
            "physical_suffering",
        ),
        (
            6,
            "Frequent colds or upper respiratory infections",
            "Rhumes ou infections respiratoires fréquents",
            "نزلات برد أو عدوى تنفسية متكررة",
            "physical_suffering",
        ),
        (
            7,
            "Nasal discharge or runny nose",
            "Écoulement nasal",
            "سيلان الأنف",
            "physical_suffering",
        ),
        (
            8,
            "Difficulty swallowing foods",
            "Difficulté à avaler les aliments",
            "صعوبة بلع الطعام",
            "physical_suffering",
        ),
        (
            9,
            "Mood swings or temper tantrums",
            "Sautes d'humeur ou colères",
            "تقلبات مزاج أو نوبات غضب",
            "emotional_distress",
        ),
        (
            10,
            "Aggressive or hyperactive behavior",
            "Comportement agressif ou hyperactif",
            "سلوك عدواني أو فرط نشاط",
            "emotional_distress",
        ),
        (
            11,
            "Discipline problems",
            "Problèmes de discipline",
            "مشاكل انضباط",
            "emotional_distress",
        ),
        (
            12,
            "Excessive daytime drowsiness or napping",
            "Somnolence diurne excessive ou siestes",
            "نعاس نهاري زائد أو قيلولة",
            "daytime_problems",
        ),
        (
            13,
            "Poor attention span or concentration",
            "Mauvaise attention ou concentration",
            "ضعف انتباه أو تركيز",
            "daytime_problems",
        ),
        (
            14,
            "Difficulty getting out of bed in the morning",
            "Difficulté à se lever le matin",
            "صعوبة النهوض صباحاً",
            "daytime_problems",
        ),
        (
            15,
            "Worried over your child's general health",
            "Inquiétude pour la santé générale de l'enfant",
            "قلق على الصحة العامة للطفل",
            "caregiver_concerns",
        ),
        (
            16,
            "Concern that your child is not getting enough air",
            "Crainte que l'enfant ne reçoive pas assez d'air",
            "قلق من عدم حصول الطفل على كافية الهواء",
            "caregiver_concerns",
        ),
        (
            17,
            "Sleep problem interferes with your daily activities",
            "Le trouble du sommeil gêne vos activités quotidiennes",
            "مشكلة النوم تعيق أنشطتكم اليومية",
            "caregiver_concerns",
        ),
        (
            18,
            "Frustrated with your child's sleep condition",
            "Frustration face au sommeil de l'enfant",
            "إحباط من وضع نوم الطفل",
            "caregiver_concerns",
        ),
    )
)

LICENSE_SNOT22 = (
    "FLAG [COMMERCIAL LICENCE REQUIRED]: Copyright Washington University in "
    "St. Louis. Commercial/EHR use requires licensing from Washington "
    "University OTM."
)
LICENSE_NOSE = (
    "FLAG [VERIFY COMMERCIAL REDISTRIBUTION]: Copyright AAO-HNS Foundation / "
    "publisher (Stewart et al. 2004). Verify commercial EHR permissions."
)
LICENSE_THI = (
    "FLAG [VERIFY COMMERCIAL REDISTRIBUTION]: Published in Arch Otolaryngol "
    "Head Neck Surg (AMA, 1996). Verify commercial EHR rights."
)
LICENSE_DHI = (
    "FLAG [VERIFY COMMERCIAL REDISTRIBUTION]: Published in Arch Otolaryngol "
    "Head Neck Surg (AMA, 1990). Verify commercial EHR redistribution rights."
)
LICENSE_VHI10 = (
    "FLAG [VERIFY COMMERCIAL REDISTRIBUTION]: Published in Laryngoscope "
    "(Rosen et al. 2004). Verify commercial software permissions."
)
LICENSE_RSI = (
    "FLAG [VERIFY COMMERCIAL REDISTRIBUTION]: Published in J Voice "
    "(Belafsky et al. 2002). Verify commercial EHR permissions."
)
LICENSE_EAT10 = (
    "FLAG [COMMERCIAL LICENCE REQUIRED]: Copyright Societe des Produits Nestle "
    "S.A., distributed via Mapi Research Trust (ePROVIDE). Commercial digital "
    "use requires licensing."
)
LICENSE_EPWORTH = (
    "FLAG [COMMERCIAL LICENCE REQUIRED]: Copyright Dr. Murray Johns "
    "(1990-1997), distributed via Mapi Research Trust (ePROVIDE). "
    "Commercial/electronic use requires licensing."
)
LICENSE_STOPBANG = (
    "FLAG [COMMERCIAL LICENCE REQUIRED]: Copyright University Health Network "
    "(UHN), Toronto, Canada (stopbang.ca). Commercial/electronic EHR use "
    "requires a UHN licence."
)
LICENSE_OSA18 = (
    "FLAG [VERIFY COMMERCIAL REDISTRIBUTION]: Published in Otolaryngol Head "
    "Neck Surg (Franco et al. 2000). Verify commercial EHR permissions."
)

LAUNCH_INSTRUMENT_SPECS: tuple[LaunchInstrumentSpec, ...] = (
    LaunchInstrumentSpec(
        code="snot22",
        category="sinonasal",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=110,
        mcid=Decimal("8.90"),
        license_note=LICENSE_SNOT22,
        reference=(
            "Hopkins C et al. Clin Otolaryngol. 2009;34(5):447-454; "
            "Piccirillo JF et al. Otolaryngol Head Neck Surg. 2002;126(1):41-47."
        ),
        scale_key="likert_0_5",
        scale_multiplier=Decimal("1"),
        title_en="SNOT-22",
        title_fr="SNOT-22",
        title_ar="SNOT-22",
        items=_SNOT22_ITEMS,
        severity_bands=(
            _band("normal", 0, 7),
            _band("mild", 8, 20),
            _band("moderate", 21, 50),
            _band("severe", 51, 110),
        ),
        subscales=(
            SubscaleDef("rhinologic", ("q1", "q2", "q3", "q4", "q5")),
            SubscaleDef("extranasal", ("q6", "q7", "q8")),
            SubscaleDef("ear_facial", ("q9", "q10", "q11", "q12")),
            SubscaleDef("sleep", ("q13", "q14", "q15", "q16")),
            SubscaleDef(
                "psychological",
                ("q17", "q18", "q19", "q20", "q21", "q22"),
            ),
        ),
    ),
    LaunchInstrumentSpec(
        code="nose",
        category="sinonasal",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=100,
        mcid=Decimal("19.40"),
        license_note=LICENSE_NOSE,
        reference=(
            "Stewart MG et al. Otolaryngol Head Neck Surg. 2004;130(2):157-163; "
            "Lipan MJ, Most SP. JAMA Facial Plast Surg. 2013;15(5):358-361."
        ),
        scale_key="likert_0_4",
        scale_multiplier=Decimal("5"),
        title_en="NOSE",
        title_fr="NOSE",
        title_ar="NOSE",
        items=_NOSE_ITEMS,
        severity_bands=(
            _band("none", 0, 0),
            _band("mild", 5, 25),
            _band("moderate", 30, 50),
            _band("severe", 55, 75),
            _band("extreme", 80, 100),
        ),
    ),
    LaunchInstrumentSpec(
        code="thi",
        category="ear",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=100,
        mcid=Decimal("7.00"),
        license_note=LICENSE_THI,
        reference=(
            "Newman CW, Jacobson GP, Spitzer JB. Arch Otolaryngol Head Neck Surg. "
            "1996;122(2):143-148."
        ),
        scale_key="thi_dhi",
        scale_multiplier=Decimal("1"),
        title_en="Tinnitus Handicap Inventory",
        title_fr="Inventaire de handicap lié aux acouphènes",
        title_ar="مقياس إعاقة الطنين",
        items=_THI_ITEMS,
        severity_bands=(
            _band("slight", 0, 16),
            _band("mild", 18, 36),
            _band("moderate", 38, 56),
            _band("severe", 58, 76),
            _band("catastrophic", 78, 100),
        ),
        subscales=(
            SubscaleDef(
                "functional",
                (
                    "t1",
                    "t2",
                    "t4",
                    "t7",
                    "t9",
                    "t12",
                    "t13",
                    "t15",
                    "t18",
                    "t20",
                    "t24",
                ),
            ),
            SubscaleDef(
                "emotional",
                ("t3", "t6", "t10", "t14", "t16", "t17", "t21", "t22", "t25"),
            ),
            SubscaleDef("catastrophic", ("t5", "t8", "t11", "t19", "t23")),
        ),
    ),
    LaunchInstrumentSpec(
        code="dhi",
        category="vertigo",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=100,
        mcid=Decimal("18.00"),
        license_note=LICENSE_DHI,
        reference=(
            "Jacobson GP, Newman CW. Arch Otolaryngol Head Neck Surg. "
            "1990;116(4):424-427; Whitney SL et al. Otol Neurotol. "
            "2004;25(2):139-143."
        ),
        scale_key="thi_dhi",
        scale_multiplier=Decimal("1"),
        title_en="Dizziness Handicap Inventory",
        title_fr="Inventaire de handicap lié aux vertiges",
        title_ar="مقياس إعاقة الدوار",
        items=_DHI_ITEMS,
        severity_bands=(
            _band("none", 0, 14),
            _band("mild", 16, 34),
            _band("moderate", 36, 52),
            _band("severe", 54, 100),
        ),
        subscales=(
            SubscaleDef(
                "physical",
                ("d1", "d4", "d8", "d11", "d13", "d17", "d25"),
            ),
            SubscaleDef(
                "emotional",
                ("d2", "d9", "d10", "d15", "d18", "d20", "d21", "d22", "d23"),
            ),
            SubscaleDef(
                "functional",
                ("d3", "d5", "d6", "d7", "d12", "d14", "d16", "d19", "d24"),
            ),
        ),
    ),
    LaunchInstrumentSpec(
        code="vhi10",
        category="voice",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=40,
        mcid=Decimal("4.00"),
        license_note=LICENSE_VHI10,
        reference=(
            "Rosen CA et al. Laryngoscope. 2004;114(9):1549-1556; "
            "Arffa RE et al. J Voice. 2012;26(4):462-465."
        ),
        scale_key="vhi_0_4",
        scale_multiplier=Decimal("1"),
        title_en="Voice Handicap Index-10",
        title_fr="Indice de handicap vocal-10",
        title_ar="مؤشر إعاقة الصوت-10",
        items=_VHI10_ITEMS,
        severity_bands=(
            _band("normal", 0, 11),
            _band("abnormal", 12, 40),
        ),
        subscales=(
            SubscaleDef("functional", ("v1", "v3", "v5", "v6", "v8")),
            SubscaleDef("physical", ("v2", "v4", "v10")),
            SubscaleDef("emotional", ("v7", "v9")),
        ),
    ),
    LaunchInstrumentSpec(
        code="rsi",
        category="reflux",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=45,
        mcid=None,
        license_note=LICENSE_RSI,
        reference="Belafsky PC, Postma GN, Koufman JA. J Voice. 2002;16(2):274-277.",
        scale_key="likert_0_5_rsi",
        scale_multiplier=Decimal("1"),
        title_en="Reflux Symptom Index",
        title_fr="Indice des symptômes de reflux",
        title_ar="مؤشر أعراض الارتجاع",
        items=_RSI_ITEMS,
        severity_bands=(
            _band("normal", 0, 13),
            _band("abnormal", 14, 45),
        ),
    ),
    LaunchInstrumentSpec(
        code="eat10",
        category="swallowing",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=40,
        mcid=None,
        license_note=LICENSE_EAT10,
        reference=(
            "Belafsky PC et al. Ann Otol Rhinol Laryngol. 2008;117(12):919-924."
        ),
        scale_key="likert_0_4",
        scale_multiplier=Decimal("1"),
        title_en="Eating Assessment Tool-10",
        title_fr="Outil d'évaluation de la déglutition-10",
        title_ar="أداة تقييم البلع-10",
        items=_EAT10_ITEMS,
        severity_bands=(
            _band("normal", 0, 2),
            _band("abnormal", 3, 40),
        ),
    ),
    LaunchInstrumentSpec(
        code="epworth",
        category="sleep",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=24,
        mcid=Decimal("2.00"),
        license_note=LICENSE_EPWORTH,
        reference="Johns MW. Sleep. 1991;14(6):540-545.",
        scale_key="epworth",
        scale_multiplier=Decimal("1"),
        title_en="Epworth Sleepiness Scale",
        title_fr="Échelle de somnolence d'Epworth",
        title_ar="مقياس النعاس إبورث",
        items=_EPWORTH_ITEMS,
        severity_bands=(
            _band("normal", 0, 10),
            _band("mild", 11, 12),
            _band("moderate", 13, 15),
            _band("severe", 16, 24),
        ),
    ),
    LaunchInstrumentSpec(
        code="stopbang",
        category="sleep",
        respondent="patient",
        scoring_type="sum",
        min_score=0,
        max_score=8,
        mcid=None,
        license_note=LICENSE_STOPBANG,
        reference=(
            "Chung F et al. Anesthesiology. 2008;108(5):812-821; "
            "Chung F et al. Chest. 2016;149(3):631-638."
        ),
        scale_key="yes_no",
        scale_multiplier=Decimal("1"),
        title_en="STOP-Bang Questionnaire",
        title_fr="Questionnaire STOP-Bang",
        title_ar="استبيان STOP-Bang",
        items=_STOPBANG_ITEMS,
        severity_bands=(
            _band("low", 0, 2),
            _band("intermediate", 3, 4),
            _band("high", 5, 8),
        ),
    ),
    LaunchInstrumentSpec(
        code="osa18",
        category="sleep",
        respondent="parent",
        scoring_type="sum",
        min_score=18,
        max_score=126,
        mcid=None,
        license_note=LICENSE_OSA18,
        reference=(
            "Franco RA Jr, Rosenfeld RM, Rao M. Otolaryngol Head Neck Surg. "
            "2000;123(1 Pt 1):9-16."
        ),
        scale_key="osa_1_7",
        scale_multiplier=Decimal("1"),
        title_en="OSA-18",
        title_fr="OSA-18",
        title_ar="OSA-18",
        items=_OSA18_ITEMS,
        severity_bands=(
            _band("mild", 18, 59),
            _band("moderate", 60, 80),
            _band("severe", 81, 126),
        ),
        subscales=(
            SubscaleDef(
                "sleep_disturbance",
                ("osa1", "osa2", "osa3", "osa4"),
            ),
            SubscaleDef(
                "physical_suffering",
                ("osa5", "osa6", "osa7", "osa8"),
            ),
            SubscaleDef(
                "emotional_distress",
                ("osa9", "osa10", "osa11"),
            ),
            SubscaleDef(
                "daytime_problems",
                ("osa12", "osa13", "osa14"),
            ),
            SubscaleDef(
                "caregiver_concerns",
                ("osa15", "osa16", "osa17", "osa18"),
            ),
        ),
    ),
)


def scoring_config_for_spec(spec: LaunchInstrumentSpec) -> dict[str, Any]:
    bands = [
        {
            "code": b.code,
            "minScore": str(b.min_score),
            "maxScore": str(b.max_score),
        }
        for b in spec.severity_bands
    ]
    subscales = [
        {"code": s.code, "itemCodes": list(s.item_codes)} for s in spec.subscales
    ]
    return {
        "scaleMultiplier": str(spec.scale_multiplier),
        "subscales": subscales,
        "reverseScoredItems": [],
        "severityBands": bands,
    }


def locale_translations_for_spec(
    spec: LaunchInstrumentSpec,
) -> list[dict[str, Any]]:
    option_labels = shared_option_translations(spec.scale_key)
    blocks: list[dict[str, Any]] = []
    for locale, title in (
        ("en", spec.title_en),
        ("fr", spec.title_fr),
        ("ar", spec.title_ar),
    ):
        item_texts: dict[str, str] = {}
        for item in spec.items:
            if locale == "en":
                item_texts[item.code] = item.en
            elif locale == "fr":
                item_texts[item.code] = item.fr
            else:
                item_texts[item.code] = item.ar
        blocks.append(
            {
                "locale": locale,
                "title": title,
                "items": item_texts,
                "options": option_labels[locale],
            }
        )
    return blocks


def shared_options_for_spec(spec: LaunchInstrumentSpec) -> list[dict[str, int]]:
    values = option_values_for_scale(spec.scale_key)
    return [{"value": v, "position": i + 1} for i, v in enumerate(values)]
