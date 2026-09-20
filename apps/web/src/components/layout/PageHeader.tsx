type PageHeaderProps = {
  title: string;
};

export function PageHeader({ title }: PageHeaderProps) {
  return (
    <header className="border-b border-border pb-4">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
    </header>
  );
}
