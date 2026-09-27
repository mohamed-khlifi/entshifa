import { DocumentsGate, TemplateAdminPanel } from "@/features/documents";

export default function TemplatesAdminPage() {
  return (
    <DocumentsGate admin>
      <TemplateAdminPanel />
    </DocumentsGate>
  );
}
