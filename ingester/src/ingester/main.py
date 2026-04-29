from typing import Literal

import typer
from pydantic import ValidationError
from tqdm import tqdm

from ingester.config import get_app_config
from ingester.confluence_crawler import ConfluenceSpaceCrawler
from ingester.logging import setup_logging
from ingester.vector_storage import vector_store

app = typer.Typer()


@app.command()
def crawl(
    space_key: Literal["PEX", "DCC", "PL"] = typer.Option(
        ..., "--space-key", help="Confluence space key, currently only PEX is supported"
    ),
    cql: str = typer.Option(None, "--cql", help="CQL query to filter pages"),
    include_restricted_content: bool = typer.Option(
        False, "--include-restricted-content", help="Include restricted content"
    ),
    include_attachments: bool = typer.Option(
        False, "--include-attachments", help="Include attachments"
    ),
) -> None:
    try:
        config = get_app_config()
        setup_logging(config)
        store_name = f"confluence_{space_key.lower()}"
        store = vector_store(store_name, config)
        apx_total_docs = 1000
        progress_bar = tqdm(
            desc=f"Crawling Conf space: {space_key}",
            total=apx_total_docs,
            unit="document",
            ncols=100,
            colour="green",
        )
        crawler = ConfluenceSpaceCrawler(
            app_config=config,
            vector_store=store,
            progress_bar=progress_bar,
            crawling_options={
                "space_key": space_key,
                "cql": cql,
                "include_restricted_content": include_restricted_content,
                "include_attachments": include_attachments,
                "url": config.confluence.base_url,
                "api_key": config.confluence.api_key,
                "username": config.confluence.username,
            },
        )

        crawler.crawl()
    except ValidationError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

def main() -> None:
    typer.run(crawl)


if __name__ == "__main__":
    main()
