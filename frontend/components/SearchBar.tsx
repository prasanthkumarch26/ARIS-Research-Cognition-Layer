"use client";

import { Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

export default function SearchBar() {
  const router = useRouter();

  const [query, setQuery] = useState("");
  const [isPending, startTransition] = useTransition();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) return;

    startTransition(() => {
      router.push(`/?q=${encodeURIComponent(query)}`);
    });
  };

  return (
    <div className="sticky bottom-0 w-full py-4 bg-gradient-to-t from-black/80 to-transparent backdrop-blur">
      <div className="w-full max-w-2xl mx-auto px-2">
        {/* Loading Indicator */}
        <div
          className={`
            flex justify-center overflow-hidden
            transition-all duration-300
            ${
              isPending ? "max-h-20 opacity-100 mb-4" : "max-h-0 opacity-0 mb-0"
            }
          `}
        >
          <div
            className="
              px-4 py-2 rounded-full
              bg-[#18181b]
              border border-gray-700
              text-sm text-gray-300
              flex items-center gap-1
              shadow-md
            "
          >
            <span>Loading</span>

            <span className="animate-bounce [animation-delay:-0.3s] text-red-500">.</span>
            <span className="animate-bounce [animation-delay:-0.15s] text-red-500">.</span>
            <span className="animate-bounce text-red-500">.</span>
          </div>
        </div>

        {/* Search Box */}
        <div className="bg-[#18181b] rounded-lg p-4 sm:p-6 shadow-md">
          <form
            onSubmit={handleSearch}
            className="
              flex items-center w-full
              border border-gray-700
              rounded-md px-3 py-2
              focus-within:border-gray-500
              focus-within:ring-2 focus-within:ring-gray-700
              transition
            "
          >
            <Search size={20} className="text-gray-500 shrink-0" />

            <input
              type="text"
              placeholder="What are you researching?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="
                ml-2 w-full bg-transparent
                outline-none text-sm sm:text-base
                placeholder:text-gray-500
              "
            />
          </form>
        </div>
      </div>
    </div>
  );
}
