import { useEffect, useState } from "react";
import { Search } from "lucide-react";

interface Props {
  onSearch: (search: string, source: string, genre: string) => void;
  sources: string[];
}

export function SearchBar({ onSearch, sources }: Props) {
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [genre, setGenre] = useState("");

  useEffect(() => {
    const t = setTimeout(() => onSearch(search, source, genre), 300);
    return () => clearTimeout(t);
  }, [search, source, genre]);

  return (
    <div className="flex gap-2 items-center flex-wrap">
      <div className="relative flex-1 min-w-48">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-gray-400" />
        <input
          className="pl-8 pr-3 py-2 border rounded w-full text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
          placeholder="Search title, composer, filename…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      <select
        className="border rounded px-2 py-2 text-sm"
        value={source}
        onChange={(e) => setSource(e.target.value)}
      >
        <option value="">All sources</option>
        {sources.map((s) => <option key={s} value={s}>{s}</option>)}
      </select>
      <input
        className="border rounded px-2 py-2 text-sm w-32"
        placeholder="Genre…"
        value={genre}
        onChange={(e) => setGenre(e.target.value)}
      />
    </div>
  );
}
