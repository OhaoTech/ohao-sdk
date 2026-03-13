"""ohao CLI — entry point for all ohao tools."""

import click

API_KEYS_URL = "https://mogen3d.ohao.tech/profile"


def _make_client(api_key=None, base_url=None):
    from ohao.mogen3d.client import MoGen3DClient
    kwargs = {}
    if api_key:
        kwargs["api_key"] = api_key
    if base_url:
        kwargs["base_url"] = base_url
    return MoGen3DClient(**kwargs)


@click.group()
@click.version_option(package_name="ohao")
def main():
    """ohao — CLI & SDK for game developers."""


# ── Auth ──────────────────────────────────────────────────────────────

@main.command()
def login():
    """Log in with your MoGen3D API key."""
    import webbrowser
    from ohao._credentials import load_api_key, save_api_key

    existing = load_api_key()
    if existing:
        click.echo(f"Already logged in (key: {existing[:7]}...{existing[-4:]})")
        if not click.confirm("Replace with a new key?"):
            return

    click.echo(f"Opening {API_KEYS_URL} in your browser...")
    click.echo("Create an API key there, then paste it below.\n")
    webbrowser.open(API_KEYS_URL)

    api_key = click.prompt("API key (starts with mg_)").strip()
    if not api_key.startswith("mg_"):
        click.echo("Invalid key — must start with 'mg_'", err=True)
        raise SystemExit(1)

    # Verify the key works
    try:
        client = _make_client(api_key=api_key)
        s = client.sparks()
        client.close()
    except Exception as e:
        click.echo(f"Key verification failed: {e}", err=True)
        raise SystemExit(1)

    path = save_api_key(api_key)
    click.echo(f"\nLogged in! ({s.tier} tier, {s.balance} sparks)")
    click.echo(f"Credentials saved to {path}")


@main.command()
def logout():
    """Remove saved credentials."""
    from ohao._credentials import clear_api_key
    if clear_api_key():
        click.echo("Logged out.")
    else:
        click.echo("Not logged in.")


@main.command()
def whoami():
    """Show current account info."""
    from ohao._credentials import load_api_key
    key = load_api_key()
    if not key:
        click.echo("Not logged in. Run `ohao login` first.")
        raise SystemExit(1)

    try:
        client = _make_client(api_key=key)
        s = client.status()
        sparks = client.sparks()
        client.close()
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"Tier:    {s['tier']}")
    click.echo(f"Sparks:  {sparks.balance}")
    click.echo(f"Daily:   {s['daily_used']}/{s['daily_limit']} jobs today")
    if sparks.can_claim:
        click.echo("         Daily sparks available! Run `ohao mogen3d claim`")


# ── MoGen3D ───────────────────────────────────────────────────────────

@main.group()
def mogen3d():
    """Animation processing and retargeting."""


@mogen3d.command()
@click.option("--api-key", envvar="OHAO_API_KEY", default=None, help="API key (or set OHAO_API_KEY, or run `ohao login`).")
@click.option("--base-url", envvar="OHAO_BASE_URL", default=None)
def sparks(api_key, base_url):
    """Check your sparks balance."""
    with _make_client(api_key, base_url) as client:
        s = client.sparks()
        click.echo(f"Balance: {s.balance} sparks ({s.tier} tier)")
        click.echo(f"Daily:   +{s.daily_amount}/day")
        if s.can_claim:
            click.echo("Status:  Daily sparks available! Run `ohao mogen3d claim` to collect.")
        else:
            click.echo("Status:  Already claimed today.")


@mogen3d.command()
@click.option("--api-key", envvar="OHAO_API_KEY", default=None)
@click.option("--base-url", envvar="OHAO_BASE_URL", default=None)
def claim(api_key, base_url):
    """Claim your daily sparks."""
    with _make_client(api_key, base_url) as client:
        result = client.claim_sparks()
        click.echo(result["message"])
        click.echo(f"Balance: {result['balance']} sparks")


@mogen3d.command()
@click.option("--api-key", envvar="OHAO_API_KEY", default=None)
@click.option("--base-url", envvar="OHAO_BASE_URL", default=None)
def bundles(api_key, base_url):
    """List spark bundles available for purchase."""
    with _make_client(api_key, base_url) as client:
        for b in client.bundles():
            click.echo(f"  {b.label:<15} {b.price:>7}  (id: {b.id})")


@mogen3d.command()
@click.option("--api-key", envvar="OHAO_API_KEY", default=None)
@click.option("--base-url", envvar="OHAO_BASE_URL", default=None)
def status(api_key, base_url):
    """Show account status, tier, and usage."""
    with _make_client(api_key, base_url) as client:
        s = client.status()
        click.echo(f"Tier:    {s['tier']}")
        click.echo(f"Sparks:  {s['sparks_balance']}")
        click.echo(f"Daily:   {s['daily_used']}/{s['daily_limit']} jobs used today")
        sub = s.get("subscription")
        if sub:
            click.echo(f"Sub:     {sub['status']} (renews {sub['current_period_end'][:10]})")


# ── Process ───────────────────────────────────────────────────────────

@mogen3d.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--api-key", envvar="OHAO_API_KEY", default=None)
@click.option("--fps", type=click.Choice(["24", "30", "60"]), default="30", help="Output FPS.")
@click.option("--fbx", is_flag=True, help="Also export FBX.")
@click.option("--format", "fmt", type=click.Choice(["bvh", "fbx", "json"]), default="bvh", help="Download format.")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output file path.")
@click.option("--base-url", envvar="OHAO_BASE_URL", default=None)
def process(video_path, api_key, fps, fbx, fmt, output, base_url):
    """Upload a video and download the result. Costs 1 spark."""
    with _make_client(api_key, base_url) as client:
        s = client.sparks()
        if s.balance < 1:
            click.echo(f"Not enough sparks (balance: {s.balance}).", err=True)
            if s.can_claim:
                click.echo("Run `ohao mogen3d claim` to get your daily sparks.", err=True)
            else:
                click.echo("Purchase more at https://mogen3d.ohao.tech/pricing", err=True)
            raise SystemExit(1)

        click.echo(f"Uploading {video_path}... (1 spark will be deducted)")
        job = client.process(video_path, fps=int(fps), export_fbx=fbx)
        click.echo(f"Job {job.id} created. Waiting...")

        job = job.wait()
        if job.status == "failed":
            click.echo(f"Failed: {job.error} (spark refunded)", err=True)
            raise SystemExit(1)

        click.echo(f"Done! {job.frames} frames.")
        path = job.download(format=fmt, output_path=output)
        click.echo(f"Saved to {path}")


# ── Retarget ──────────────────────────────────────────────────────────

@mogen3d.command()
@click.argument("bvh_path", type=click.Path(exists=True))
@click.argument("character_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="Output .blend file path.")
@click.option("--preset", type=str, default=None, help="Rig preset: 'mixamo', 'ue5', or path to JSON.")
@click.option("--blender", type=click.Path(), default=None, help="Path to Blender executable.")
@click.option("--gui", is_flag=True, help="Open Blender with GUI (default: background mode).")
def retarget(bvh_path, character_path, output, preset, blender, gui):
    """Retarget a BVH animation onto a character model. Runs locally via Blender."""
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
