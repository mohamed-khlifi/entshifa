export { DocumentsGate } from "./components/DocumentsGate";
export { PatientDocumentsPanel } from "./components/PatientDocumentsPanel";
export { TemplateAdminPanel } from "./components/TemplateAdminPanel";
export { VisitDocuments } from "./components/VisitDocuments";
export {
  useCreateDocumentMutation,
  useDocumentPreviewQuery,
} from "./hooks/use-document-queries";
export {
  activeFlagCodes,
  documentKindForPlan,
  suggestedClinicalQuestion,
  type VisitDocumentKind,
} from "./lib/visit-documents";
