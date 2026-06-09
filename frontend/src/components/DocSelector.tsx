import { useQuery } from "@tanstack/react-query";
import { listDocuments } from "../lib/api";
import { FileText, ChevronDown } from "lucide-react";

interface Props {
  value: number | null;
  onChange: (id: number) => void;
  className?: string;
}

export function DocSelector({ value, onChange, className = "" }: Props) {
  const { data } = useQuery({
    queryKey: ["documents"],
    queryFn: () => listDocuments().then((r) => r.data),
  });

  const docs: any[] = data || [];

  return (
    <div className={`relative ${className}`}>
      <select
        value={value ?? ""}
        onChange={(e) => onChange(Number(e.target.value))}
        className="input-field pr-10 appearance-none cursor-pointer"
      >
        <option value="" disabled>Select a document…</option>
        {docs.map((d: any) => (
          <option key={d.id} value={d.id}>
            {d.original_filename} ({d.word_count?.toLocaleString()} words)
          </option>
        ))}
      </select>
      <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
    </div>
  );
}
