"""ohao CLI — entry point for all ohao tools."""

import click


@click.group()
@click.version_option(package_name="ohao")
def main():
    """ohao — CLI & SDK for game developers."""


@main.group()
def mogen3d():
    """Motion capture: video -> BVH/FBX."""


@mogen3d.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--api-key", envvar="OHAO_API_KEY", required=True, help="MoGen3D API key (or set OHAO_API_KEY).")
@click.option("--pipeline", type=click.Choice(["2d", "3d"]), default="2d", help="Processing pipeline.")
@click.option("--fps", type=int, default=30, help="Output FPS.")
@click.option("--format", "fmt", type=click.Choice(["bvh", "fbx", "json"]), default="bvh", help="Download format.")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path.")
@click.option("--base-url", envvar="OHAO_BASE_URL", default=None, help="API base URL override.")
def process(video_path, api_key, pipeline, fps, fmt, output, base_url):
    """Upload a video, process it, and download the result."""
    from ohao.mogen3d.client import MoGen3DClient

    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url

    with MoGen3DClient(**kwargs) as client:
        click.echo(f"Uploading {video_path}...")
        job = client.upload(video_path, pipeline=pipeline, fps=fps)
        click.echo(f"Job {job.id} created. Waiting for completion...")

        job = job.wait()
        if job.status == "failed":
            click.echo(f"Job failed: {job.error}", err=True)
            raise SystemExit(1)

        click.echo(f"Done! {job.frames} frames extracted.")
        path = job.download(format=fmt, output_path=output)
        click.echo(f"Saved to {path}")


@mogen3d.command()
@click.argument("bvh_path", type=click.Path(exists=True))
@click.argument("character_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Output .blend file path.")
@click.option("--preset", type=str, default=None, help="Rig preset: 'mixamo', 'ue5', or path to JSON.")
@click.option("--blender", type=click.Path(), default=None, help="Path to Blender executable.")
@click.option("--gui", is_flag=True, help="Open Blender with GUI (default: background mode).")
def retarget(bvh_path, character_path, output, preset, blender, gui):
    """Retarget a BVH animation onto a character model using Blender."""
    from ohao.mogen3d.retarget import retarget as do_retarget

    click.echo(f"Retargeting {bvh_path} -> {character_path}...")
    path = do_retarget(
        bvh_path,
        character_path,
        output_path=output,
        preset=preset,
        blender_path=blender,
        background=not gui,
    )
    click.echo(f"Saved to {path}")
