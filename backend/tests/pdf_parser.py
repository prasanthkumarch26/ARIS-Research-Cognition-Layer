import httpx
import fitz
import sys
import asyncio


async def download_parse_pdf(pdf_url: str):
    try:
        async with httpx.AsyncClient() as client:
            print(f"Downloading: {pdf_url}")

            response = await client.get(pdf_url, timeout=60.0)
            response.raise_for_status()

            pdf_data = response.content

            # Open PDF from bytes
            doc = fitz.open(stream=pdf_data, filetype="pdf")

            print(f"Success: Downloaded and parsed {pdf_url} into {doc.page_count} pages")


            def get_body_font_size(doc) -> float:
                size_counts = {}
                body_size = 11
                headers = []
                has_reached_abstract = False

                for page in doc:
                    page_dict = page.get_text("dict")

                    for block in page_dict.get("blocks", []):
                        if block.get("type") != 0:
                            continue

                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                font_size = round(span["size"], 1)

                                # Count characters instead of spans
                                text_length = len(span["text"].strip())

                                if text_length == 0:
                                    continue

                                size_counts[font_size] = (
                                    size_counts.get(font_size, 0) + text_length
                                )

                                if (span["text"] == "Abstract"):
                                    has_reached_abstract = True
                                if has_reached_abstract:
                                    if span["size"] > body_size and span["text"].istitle():
                                        headers.append(span["text"])
                                else:
                                    continue


                if not size_counts:
                    return None

                # return max(size_counts.items(), key=lambda x: x[1])[0]
                return headers

            res = get_body_font_size(doc)
            print(res)
            doc.close()

    except httpx.HTTPError as e:
        print(f"HTTP Error while downloading PDF: {e}")

    except Exception as e:
        print(f"Error while parsing PDF {pdf_url}: {e}")

    finally:
        sys.exit(1)


async def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <pdf-url>")
        sys.exit(1)

    pdf_url = sys.argv[1]

    await download_parse_pdf(pdf_url)


if __name__ == "__main__":
    asyncio.run(main())