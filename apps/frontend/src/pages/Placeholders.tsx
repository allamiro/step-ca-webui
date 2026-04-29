type Props = { title: string; description: string };

export function PlaceholderPage({ title, description }: Props) {
  return (
    <div className="p-6">
      <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        <p className="text-slate-400">{description}</p>
      </div>
    </div>
  );
}
