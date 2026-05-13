"use client";

import SearchBar from "@/components/SearchBar";

export default function Error({
  error,
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  // Extract status code if present in message
  const statusMatch = error.message.match(/\d+/);
  const statusCode = statusMatch ? statusMatch[0] : "Error";

  return (
    <main className="min-h-screen flex flex-col px-4 py-6">
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

      {/* Error Content */}
      <div className="flex-1 flex flex-col items-center justify-center text-center">
        <h1 className="text-6xl sm:text-7xl font-bold text-red-500">
          {statusCode}
        </h1>

        <p className="text-gray-400 mt-4 text-sm sm:text-base">
          Something went wrong while fetching papers.
        </p>

        <button
          onClick={() => reset()}
          className="mt-6 px-5 py-2 rounded-xl border border-gray-700 hover:border-red-500 transition-colors"
        >
          Try Again
        </button>
      </div>

      {/* Bottom Search Bar */}
      <SearchBar />
    </main>
  );
}
