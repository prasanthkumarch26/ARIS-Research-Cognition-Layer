type Paper = {
  arxiv_id: string;
  title: string;
  abstract: string;
  authors: string[];
  pdf_url: string;
  matching_chunk: string;
  rank: number;
};

export default function PaperCard({ paper }: { paper: Paper }) {
  return (
    <div className="border border-gray-800 rounded-lg p-4 hover:bg-[#1f1f23] transition cursor-pointer">
      <h1 className="font-semibold text-white">{paper.title}</h1>

      <p className="text-xs sm:text-sm text-gray-400 mt-1">
        {paper.authors.slice(0, 3).join(", ")}
        {paper.authors.length > 3 && "..."}
      </p>

      <p className="text-sm text-gray-300 mt-3 line-clamp-3">
        {paper.matching_chunk}
      </p>

      {/* <p className="text-xs text-gray-500 mt-2 line-clamp-2">
        {paper.abstract}
      </p> */}

      <div className="flex gap-4 mt-3 text-sm">
        <a
          href={paper.pdf_url}
          target="_blank"
          className="text-blue-400 hover:underline"
        >
          View PDF
        </a>

        <a
          href={paper.arxiv_id}
          target="_blank"
          className="text-gray-400 hover:underline"
        >
          arXiv
        </a>
      </div>
    </div>
  );
}
