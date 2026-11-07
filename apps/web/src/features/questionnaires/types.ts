/** Questionnaire flow API shapes (P5-03). Regenerated types may extend these. */

export type PublicInstrumentOption = {
  value: number;
  position: number;
  text: string;
};

export type PublicInstrumentItem = {
  code: string;
  position: number;
  text: string;
  options: PublicInstrumentOption[];
};

export type PublicQuestionnaireSession = {
  patientFirstName: string;
  clinicName: string;
  locale: string;
  channel: string;
  expiresAt: string;
  instrument: {
    code: string;
    title: string;
    category: string;
    respondent: string;
    items: PublicInstrumentItem[];
  };
};

export type QuestionnaireResponseSummary = {
  publicId: string;
  instrumentCode: string;
  instrumentTitle: string | null;
  locale: string;
  enteredBy: string;
  completedAt: string;
  totalScore: string;
  subscaleScores: Record<string, string>;
  severityBand: string | null;
  changeFromPrevious: string | null;
  mcidReached: boolean | null;
  encounterId: string | null;
};

export type QuestionnaireInvitationCreated = {
  publicId: string;
  instrumentCode: string;
  channel: string;
  context: string;
  locale: string;
  sentAt: string;
  expiresAt: string;
  token: string;
  publicPath: string;
};

export type PageSchema<T> = {
  items: T[];
  page: { total: number; limit: number; offset: number };
};
