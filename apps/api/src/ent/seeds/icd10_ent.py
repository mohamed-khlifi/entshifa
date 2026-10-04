"""Curated ICD-10 ENT diagnoses plus a parallel LOCAL system (feature spec §20).

This is a clinic snapshot, not a live WHO feed. Codes referenced by visit
templates are included so complaint favourites resolve. Displays are en and fr.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ent.core.utils.ids import new_ulid
from ent.features.terminology.models import (
    CodeSystem,
    Concept,
    ConceptRelationship,
    ConceptTranslation,
    ValueSet,
    ValueSetMember,
)

ICD10_SYSTEM_CODE = "ICD10"
LOCAL_SYSTEM_CODE = "LOCAL"
ENT_DIAGNOSES_VALUE_SET = "ent.diagnoses"

# code|english|french — WHO ICD-10 titles used in ENT practice.
_ICD_TABLE = """
C07|Malignant neoplasm of parotid gland|Tumeur maligne de la parotide
C08.0|Malignant neoplasm of submandibular gland|Tumeur maligne de la glande sous-mandibulaire
C08.9|Malignant neoplasm of major salivary gland, unspecified|Tumeur maligne d'une glande salivaire principale, sans précision
C09.9|Malignant neoplasm of tonsil, unspecified|Tumeur maligne de l'amygdale, sans précision
C10.9|Malignant neoplasm of oropharynx, unspecified|Tumeur maligne de l'oropharynx, sans précision
C11.9|Malignant neoplasm of nasopharynx, unspecified|Tumeur maligne du rhinopharynx, sans précision
C13.9|Malignant neoplasm of hypopharynx, unspecified|Tumeur maligne de l'hypopharynx, sans précision
C30.0|Malignant neoplasm of nasal cavity|Tumeur maligne de la fosse nasale
C31.9|Malignant neoplasm of accessory sinus, unspecified|Tumeur maligne d'un sinus de la face, sans précision
C32.9|Malignant neoplasm of larynx, unspecified|Tumeur maligne du larynx, sans précision
C73|Malignant neoplasm of thyroid gland|Tumeur maligne de la thyroïde
G43.9|Migraine, unspecified|Migraine, sans précision
G44.8|Other specified headache syndromes|Autres syndromes d'algies céphaliques précisés
H60.0|Abscess of external ear|Abcès de l'oreille externe
H60.1|Cellulitis of external ear|Cellulite de l'oreille externe
H60.3|Other infective otitis externa|Autres otites externes infectieuses
H60.4|Cholesteatoma of external ear|Cholestéatome de l'oreille externe
H60.5|Acute otitis externa, noninfective|Otite externe aiguë, non infectieuse
H60.8|Other otitis externa|Autres otites externes
H60.9|Otitis externa, unspecified|Otite externe, sans précision
H61.0|Perichondritis of external ear|Périchondrite de l'oreille externe
H61.1|Noninfective disorders of pinna|Affections non infectieuses du pavillon
H61.2|Impacted cerumen|Bouchon de cérumen
H65.0|Acute serous otitis media|Otite moyenne séreuse aiguë
H65.1|Other acute nonsuppurative otitis media|Autres otites moyennes aiguës, non suppurées
H65.2|Chronic serous otitis media|Otite moyenne séreuse chronique
H65.3|Chronic mucoid otitis media|Otite moyenne mucoïde chronique
H65.4|Other chronic nonsuppurative otitis media|Autres otites moyennes chroniques, non suppurées
H65.9|Nonsuppurative otitis media, unspecified|Otite moyenne non suppurée, sans précision
H66.0|Acute suppurative otitis media|Otite moyenne aiguë suppurée
H66.1|Chronic tubotympanic suppurative otitis media|Otite moyenne chronique suppurée tubo-tympanique
H66.2|Chronic atticoantral suppurative otitis media|Otite moyenne chronique suppurée attico-antrale
H66.3|Other chronic suppurative otitis media|Autres otites moyennes chroniques suppurées
H66.4|Suppurative otitis media, unspecified|Otite moyenne suppurée, sans précision
H66.9|Otitis media, unspecified|Otite moyenne, sans précision
H68.1|Obstruction of Eustachian tube|Obstruction de la trompe d'Eustache
H69.0|Patulous Eustachian tube|Béance de la trompe d'Eustache
H70.0|Acute mastoiditis|Mastoïdite aiguë
H70.1|Chronic mastoiditis|Mastoïdite chronique
H71.9|Cholesteatoma of middle ear, unspecified|Cholestéatome de l'oreille moyenne, sans précision
H72.0|Central perforation of tympanic membrane|Perforation centrale du tympan
H72.1|Attic perforation of tympanic membrane|Perforation atticale du tympan
H72.9|Perforation of tympanic membrane, unspecified|Perforation du tympan, sans précision
H73.0|Acute myringitis|Myringite aiguë
H74.0|Tympanosclerosis|Tympanosclérose
H74.1|Adhesive middle ear disease|Otite moyenne adhésive
H74.2|Discontinuity and dislocation of ear ossicles|Discontinuité et luxation des osselets
H74.3|Other acquired abnormalities of ear ossicles|Autres anomalies acquises des osselets
H80.0|Otosclerosis involving oval window, nonobliterative|Otospongiose de la fenêtre ovale, non oblitérante
H80.9|Otosclerosis, unspecified|Otospongiose, sans précision
H81.0|Meniere disease|Maladie de Ménière
H81.1|Benign paroxysmal vertigo|Vertige paroxystique bénin
H81.2|Vestibular neuronitis|Neuronite vestibulaire
H81.3|Other peripheral vertigo|Autres vertiges périphériques
H81.4|Vertigo of central origin|Vertige d'origine centrale
H81.8|Other disorders of vestibular function|Autres atteintes de la fonction vestibulaire
H81.9|Disorder of vestibular function, unspecified|Atteinte de la fonction vestibulaire, sans précision
H83.0|Labyrinthitis|Labyrinthite
H83.3|Noise effects on inner ear|Effets du bruit sur l'oreille interne
H90.0|Conductive hearing loss, bilateral|Surdité de transmission bilatérale
H90.1|Conductive hearing loss, unilateral with unrestricted hearing on the contralateral side|Surdité de transmission unilatérale, audition non restreinte de l'autre côté
H90.2|Conductive hearing loss, unspecified|Surdité de transmission, sans précision
H90.3|Sensorineural hearing loss, bilateral|Surdité neurosensorielle bilatérale
H90.4|Sensorineural hearing loss, unilateral with unrestricted hearing on the contralateral side|Surdité neurosensorielle unilatérale, audition non restreinte de l'autre côté
H90.5|Sensorineural hearing loss, unspecified|Surdité neurosensorielle, sans précision
H90.6|Mixed conductive and sensorineural hearing loss, bilateral|Surdité mixte bilatérale
H90.7|Mixed conductive and sensorineural hearing loss, unilateral with unrestricted hearing on the contralateral side|Surdité mixte unilatérale, audition non restreinte de l'autre côté
H90.8|Mixed conductive and sensorineural hearing loss, unspecified|Surdité mixte, sans précision
H91.0|Ototoxic hearing loss|Perte auditive ototoxique
H91.1|Presbycusis|Presbyacousie
H91.2|Sudden idiopathic hearing loss|Perte auditive brusque idiopathique
H91.9|Hearing loss, unspecified|Perte auditive, sans précision
H92.0|Otalgia|Otalgie
H92.1|Otorrhoea|Otorrhée
H92.2|Otorrhagia|Otorragie
H93.0|Degenerative and vascular disorders of ear|Affections dégénératives et vasculaires de l'oreille
H93.1|Tinnitus|Acouphènes
H93.2|Other abnormal auditory perceptions|Autres perceptions auditives anormales
H93.3|Disorders of acoustic nerve|Affections du nerf auditif
H95.0|Recurrent cholesteatoma of postmastoidectomy cavity|Cholestéatome récidivant de la cavité post-mastoïdectomie
H95.1|Other disorders following mastoidectomy|Autres affections après mastoïdectomie
J00|Acute nasopharyngitis|Rhinopharyngite aiguë
J01.0|Acute maxillary sinusitis|Sinusite maxillaire aiguë
J01.1|Acute frontal sinusitis|Sinusite frontale aiguë
J01.2|Acute ethmoidal sinusitis|Sinusite ethmoïdale aiguë
J01.3|Acute sphenoidal sinusitis|Sinusite sphénoïdale aiguë
J01.4|Acute pansinusitis|Pansinusite aiguë
J01.9|Acute sinusitis, unspecified|Sinusite aiguë, sans précision
J02.0|Streptococcal pharyngitis|Pharyngite à streptocoques
J02.9|Acute pharyngitis, unspecified|Pharyngite aiguë, sans précision
J03.0|Streptococcal tonsillitis|Amygdalite à streptocoques
J03.9|Acute tonsillitis, unspecified|Amygdalite aiguë, sans précision
J04.0|Acute laryngitis|Laryngite aiguë
J04.1|Acute tracheitis|Trachéite aiguë
J04.2|Acute laryngotracheitis|Laryngotrachéite aiguë
J06.9|Acute upper respiratory infection, unspecified|Infection aiguë des voies respiratoires supérieures, sans précision
J30.0|Vasomotor rhinitis|Rhinite vasomotrice
J30.1|Allergic rhinitis due to pollen|Rhinite allergique due au pollen
J30.2|Other seasonal allergic rhinitis|Autre rhinite allergique saisonnière
J30.8|Other allergic rhinitis|Autres rhinites allergiques
J30.9|Allergic rhinitis, unspecified|Rhinite allergique, sans précision
J31.0|Chronic rhinitis|Rhinite chronique
J31.1|Chronic nasopharyngitis|Rhinopharyngite chronique
J31.2|Chronic pharyngitis|Pharyngite chronique
J32.0|Chronic maxillary sinusitis|Sinusite maxillaire chronique
J32.1|Chronic frontal sinusitis|Sinusite frontale chronique
J32.2|Chronic ethmoidal sinusitis|Sinusite ethmoïdale chronique
J32.3|Chronic sphenoidal sinusitis|Sinusite sphénoïdale chronique
J32.4|Chronic pansinusitis|Pansinusite chronique
J32.8|Other chronic sinusitis|Autres sinusites chroniques
J32.9|Chronic sinusitis, unspecified|Sinusite chronique, sans précision
J33.0|Polyp of nasal cavity|Polype de la fosse nasale
J33.1|Polypoid sinus degeneration|Dégénérescence polypoïde d'un sinus
J33.8|Other polyp of sinus|Autres polypes des sinus
J33.9|Nasal polyp, unspecified|Polype nasal, sans précision
J34.0|Abscess, furuncle and carbuncle of nose|Abcès, furoncle et anthrax du nez
J34.1|Cyst and mucocele of nose and nasal sinus|Kyste et mucocèle du nez et des sinus
J34.2|Deviated nasal septum|Déviation de la cloison nasale
J34.3|Hypertrophy of nasal turbinates|Hypertrophie des cornets du nez
J34.8|Other specified disorders of nose and nasal sinuses|Autres affections précisées du nez et des sinus
J35.0|Chronic tonsillitis|Amygdalite chronique
J35.1|Hypertrophy of tonsils|Hypertrophie des amygdales
J35.2|Hypertrophy of adenoids|Hypertrophie des végétations adénoïdes
J35.3|Hypertrophy of tonsils with hypertrophy of adenoids|Hypertrophie des amygdales avec hypertrophie des végétations adénoïdes
J35.8|Other chronic diseases of tonsils and adenoids|Autres maladies chroniques des amygdales et des végétations adénoïdes
J36|Peritonsillar abscess|Abcès péri-amygdalien
J37.0|Chronic laryngitis|Laryngite chronique
J37.1|Chronic laryngotracheitis|Laryngotrachéite chronique
J38.0|Paralysis of vocal cords and larynx|Paralysie des cordes vocales et du larynx
J38.1|Polyp of vocal cord and larynx|Polype des cordes vocales et du larynx
J38.2|Nodules of vocal cords|Nodules des cordes vocales
J38.3|Other diseases of vocal cords|Autres maladies des cordes vocales
J38.4|Oedema of larynx|Œdème du larynx
J38.7|Other diseases of larynx|Autres maladies du larynx
J39.0|Retropharyngeal and parapharyngeal abscess|Abcès rétropharyngé et parapharyngé
J39.2|Other diseases of pharynx|Autres maladies du pharynx
K07.6|Temporomandibular joint disorders|Lésions de l'articulation temporo-mandibulaire
K11.2|Sialoadenitis|Sialadénite
K11.5|Sialolithiasis|Sialolithiase
K11.7|Disturbances of salivary secretion|Troubles de la sécrétion salivaire
K12.0|Recurrent oral aphthae|Aphte buccal récidivant
K12.1|Other forms of stomatitis|Autres formes de stomatite
K13.0|Diseases of lips|Maladies des lèvres
K13.7|Other and unspecified lesions of oral mucosa|Autres lésions et lésions sans précision de la muqueuse buccale
K14.0|Glossitis|Glossite
K14.6|Glossodynia|Glossodynie
R04.0|Epistaxis|Épistaxis
R13|Dysphagia|Dysphagie
R42|Dizziness and giddiness|Étourdissements et vertiges
R49.0|Dysphonia|Dysphonie
R49.1|Aphonia|Aphonie
R49.8|Other and unspecified voice disturbances|Autres troubles de la voix et troubles sans précision
"""

# local code, english, french, ICD-10 code it maps to
_LOCAL_TABLE = """
LOCAL.OTITIS_EXTERNA|Diffuse otitis externa|Otite externe diffuse|H60.9
LOCAL.SEPTAL_DEVIATION|Septal deviation|Déviation septale|J34.2
LOCAL.BPPV|Benign positional vertigo|Vertige positionnel bénin|H81.1
"""


def _rows(table: str) -> tuple[tuple[str, ...], ...]:
    parsed: list[tuple[str, ...]] = []
    for line in table.strip().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parsed.append(tuple(part.strip() for part in stripped.split("|")))
    return tuple(parsed)


ICD10_ENT: tuple[tuple[str, str, str], ...] = tuple(
    (code, en, fr) for code, en, fr in _rows(_ICD_TABLE)
)
LOCAL_DIAGNOSES: tuple[tuple[str, str, str, str], ...] = tuple(
    (code, en, fr, target) for code, en, fr, target in _rows(_LOCAL_TABLE)
)
ICD10_CODES = frozenset(code for code, _en, _fr in ICD10_ENT)


@dataclass(frozen=True, slots=True)
class IcdSeedReport:
    concepts: int
    translations: int
    value_sets: int
    members: int


async def seed_icd10_ent(session: AsyncSession) -> IcdSeedReport:
    """Idempotent ICD-10 ENT concepts, LOCAL parallels, and ent.diagnoses."""

    icd = await _ensure_system(
        session,
        code=ICD10_SYSTEM_CODE,
        name="ICD-10",
        version="ent-snapshot-2026",
        uri="https://icd.who.int/browse10/2019/en",
    )
    local = await _ensure_system(
        session,
        code=LOCAL_SYSTEM_CODE,
        name="Clinic local diagnoses",
        version="1",
        uri="https://entshifa.local/terminology/local",
    )
    concepts = 0
    translations = 0
    icd_by_code: dict[str, Concept] = {}
    for index, (code, en, fr) in enumerate(ICD10_ENT):
        concept, created = await _ensure_concept(
            session, system=icd, code=code, kind="diagnosis", sort_order=index
        )
        icd_by_code[code] = concept
        concepts += int(created)
        translations += await _ensure_pair(session, concept, en, fr)

    local_by_code: dict[str, Concept] = {}
    for index, (code, en, fr, _target) in enumerate(LOCAL_DIAGNOSES):
        concept, created = await _ensure_concept(
            session, system=local, code=code, kind="diagnosis", sort_order=index
        )
        local_by_code[code] = concept
        concepts += int(created)
        translations += await _ensure_pair(session, concept, en, fr)

    for code, _en, _fr, target in LOCAL_DIAGNOSES:
        await _ensure_maps_to(
            session,
            source=local_by_code[code],
            target=icd_by_code[target],
        )

    value_set, created_set = await _ensure_value_set(session)
    members = 0
    ordered = [*icd_by_code.values(), *local_by_code.values()]
    for index, concept in enumerate(ordered):
        members += await _ensure_member(session, value_set, concept, index)
    return IcdSeedReport(
        concepts=concepts,
        translations=translations,
        value_sets=1 if created_set else 0,
        members=members,
    )


async def _ensure_system(
    session: AsyncSession,
    *,
    code: str,
    name: str,
    version: str,
    uri: str,
) -> CodeSystem:
    existing = (
        await session.execute(
            select(CodeSystem).where(
                CodeSystem.code == code,
                CodeSystem.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing
    row = CodeSystem(
        public_id=new_ulid(),
        code=code,
        name=name,
        version=version,
        uri=uri,
    )
    session.add(row)
    await session.flush()
    return row


async def _ensure_concept(
    session: AsyncSession,
    *,
    system: CodeSystem,
    code: str,
    kind: str,
    sort_order: int,
) -> tuple[Concept, bool]:
    existing = (
        await session.execute(
            select(Concept).where(
                Concept.code_system_id == system.id,
                Concept.code == code,
                Concept.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.kind != kind:
            existing.kind = kind
        return existing, False
    row = Concept(
        public_id=new_ulid(),
        code_system_id=system.id,
        code=code,
        kind=kind,
        sort_order=sort_order,
        is_active=True,
        clinic_id=None,
    )
    session.add(row)
    await session.flush()
    return row, True


async def _ensure_pair(
    session: AsyncSession, concept: Concept, en: str, fr: str
) -> int:
    created = 0
    for locale, display in (("en", en), ("fr", fr)):
        existing = (
            await session.execute(
                select(ConceptTranslation).where(
                    ConceptTranslation.concept_id == concept.id,
                    ConceptTranslation.locale == locale,
                    ConceptTranslation.clinic_id.is_(None),
                    ConceptTranslation.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(
            ConceptTranslation(
                public_id=new_ulid(),
                concept_id=concept.id,
                locale=locale,
                display=display,
                full_name=display,
                clinic_id=None,
            )
        )
        created += 1
    await session.flush()
    return created


async def _ensure_maps_to(
    session: AsyncSession, *, source: Concept, target: Concept
) -> None:
    existing = (
        await session.execute(
            select(ConceptRelationship).where(
                ConceptRelationship.source_concept_id == source.id,
                ConceptRelationship.target_concept_id == target.id,
                ConceptRelationship.type == "maps_to",
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        ConceptRelationship(
            public_id=new_ulid(),
            source_concept_id=source.id,
            target_concept_id=target.id,
            type="maps_to",
        )
    )
    await session.flush()


async def _ensure_value_set(session: AsyncSession) -> tuple[ValueSet, bool]:
    existing = (
        await session.execute(
            select(ValueSet).where(
                ValueSet.code == ENT_DIAGNOSES_VALUE_SET,
                ValueSet.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return existing, False
    row = ValueSet(
        public_id=new_ulid(),
        code=ENT_DIAGNOSES_VALUE_SET,
        name_key="terminology.valueSet.entDiagnoses",
        description_key="terminology.valueSet.entDiagnoses.description",
    )
    session.add(row)
    await session.flush()
    return row, True


async def _ensure_member(
    session: AsyncSession, value_set: ValueSet, concept: Concept, sort_order: int
) -> int:
    existing = (
        await session.execute(
            select(ValueSetMember).where(
                ValueSetMember.value_set_id == value_set.id,
                ValueSetMember.concept_id == concept.id,
                ValueSetMember.deleted_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return 0
    session.add(
        ValueSetMember(
            public_id=new_ulid(),
            value_set_id=value_set.id,
            concept_id=concept.id,
            sort_order=sort_order,
            is_default=False,
        )
    )
    await session.flush()
    return 1
