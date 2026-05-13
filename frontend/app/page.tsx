import Link from "next/link";
import PaperCard from "@/components/PaperCard";
import SearchBar from "@/components/SearchBar";

const trendingTopics = [
  "Large Language Models",
  "Retrieval Augmented Generation",
  "Computer Vision",
  "Diffusion Models",
  "AI Agents",
  "Multimodal Learning",
  "Graph Neural Networks",
  "Quantum Computing",
  "Reinforcement Learning",
  "Transformers",
];

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const params = await searchParams;
  const query = params.q;

  let results = [];

  const API_URL = process.env.NEXT_PUBLIC_API_URL;

  if (query) {
    const response = await fetch(`${API_URL}/cache/search?query=${query}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status}`);
    }

    results = await response.json();
  }

  return (
    <main className="min-h-screen flex flex-col px-4 py-6 bg-[#0e0e0e] text-white">
      {/* Header */}
      <div className="flex flex-col items-center text-center mt-4">
        <h1 className="text-2xl sm:text-3xl md:text-4xl font-semibold">
          A<span className="text-red-500">.</span>X
          <span className="text-red-500">.</span>I
          <span className="text-red-500">.</span>O
          <span className="text-red-500">.</span>M
        </h1>

        <h2 className="text-xs sm:text-sm md:text-base text-gray-400 mt-2 max-w-md">
          Adaptive eXplanatory Intelligence for Optimization and Modeling
        </h2>

        <p className="text-xs sm:text-sm text-gray-500 mt-2">
          Thank you to arXiv for use of its open access interoperability.
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 w-full max-w-2xl mx-auto mt-6">
        {query ? (
          <div className="space-y-4">
            {results.map((paper: any) => (
              <PaperCard key={paper.arxiv_id} paper={paper} />
            ))}
          </div>
        ) : (
          <div className="mt-12 flex flex-col items-center text-center">
            <h3 className="text-lg font-semibold mb-6 text-gray-200">
              Trending Topics
            </h3>

            <div className="flex flex-wrap justify-center gap-3 max-w-3xl">
              {trendingTopics.map((topic) => (
                <Link
                  key={topic}
                  href={`/?q=${encodeURIComponent(topic)}`}
                  className="
          px-4 py-2 rounded-full
          bg-[#1a1a1a]
          border border-gray-800
          text-sm text-gray-300
          hover:bg-red-500 hover:text-white
          transition-all duration-200
        "
                >
                  {topic}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Search */}
      <SearchBar />
    </main>
  );
}
