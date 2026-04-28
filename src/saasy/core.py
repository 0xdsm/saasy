import asyncio
import httpx
import yaml

from hashlib import sha256
from itertools import product
from pathlib import Path
from random import choices
from string import ascii_lowercase, digits

from rich.console import Console
console = Console()

from saasy.resources.utils import AZURE_REGIONS, AWS_REGIONS, ENVIRONMENTS

RESOURCES = Path(__file__).parent / "resources"
YAML_FILE = RESOURCES / "services.yaml"


def log(message: str, verbose: bool) -> None:
    if verbose:
        console.print(f"[bold cyan][*][/] {message}", highlight=False)


def get_regions_for_service(service_format: str) -> list[str]:
    if "azure" in service_format.lower():
        return AZURE_REGIONS
    return AWS_REGIONS


def expand_service(service: dict) -> list[dict]:
    # This function is vibecoded, I didn't know a way to do that :)

    fmt = service["format"]
    has_region = "{region}" in fmt
    has_env = "{env}" in fmt

    if not has_region and not has_env:
        return [service]

    expanded = []
    regions = get_regions_for_service(fmt) if has_region else [None]
    envs = ENVIRONMENTS if has_env else [None]

    for region, env in product(regions, envs):
        new_fmt = fmt
        name_suffix = ""

        if region:
            new_fmt = new_fmt.replace("{region}", region)
            name_suffix += f"-{region}"
        if env:
            new_fmt = new_fmt.replace("{env}", env)
            name_suffix += f"-{env}"

        expanded.append({
            "name": f"{service['name']}{name_suffix}",
            "format": new_fmt,
        })

    return expanded


def parse_services_yaml() -> list | None:
    try:
        with open(YAML_FILE, "r") as file:
            data = yaml.safe_load(file)
            return data["services"]

    except yaml.YAMLError as exception:
        console.print(f"[red][!][/] {exception}", highlight=False)
        return None
    except FileNotFoundError:
        console.print(f"[red][!][/] {YAML_FILE} file was not found", highlight=False)
        return None


def generate_random_subdomain(length: int = 40) -> str:
    return "".join(choices(ascii_lowercase + digits, k=length))


async def check_service(
    client: httpx.AsyncClient,
    service: dict,
    target: str,
    semaphore: asyncio.Semaphore,
    verbose: bool,
) -> dict | None:
    async with semaphore:
        name = service["name"]

        random_subdomain = generate_random_subdomain()
        baseline_url = service["format"].replace("{target}", random_subdomain)

        log(f'Capturing {name} baseline', verbose)

        baseline = None
        baseline_error = False

        try:
            baseline_response = await client.get(f"https://{baseline_url}", timeout=10)

            baseline = {
                "status_code": baseline_response.status_code,
                "body_size": len(baseline_response.text),
                "body_hash": sha256(baseline_response.text.encode()).hexdigest(),
            }

            log(f'{name} baseline: {baseline}', verbose)

        except httpx.RequestError as exception:
            log(f'{name} baseline failed (no wildcard DNS): {exception}', verbose)
            baseline_error = True

        target_url = service["format"].replace("{target}", target)

        try:
            target_response = await client.get(f"https://{target_url}", timeout=10)
        except httpx.RequestError as exception:
            log(f'{name} target failed: {exception}', verbose)
            return None

        result = {
            "status_code": target_response.status_code,
            "body_size": len(target_response.text),
            "body_hash": sha256(target_response.text.encode()).hexdigest(),
        }

        log(f'{name} target: {result}', verbose)

        if baseline_error:
            return {
                "service": name,
                "url": target_url,
                "baseline": None,
                "result": result,
                "no_wildcard": True,
            }

        return {
            "service": name,
            "url": target_url,
            "baseline": baseline,
            "result": result,
            "no_wildcard": False,
        }


def compare_baseline(result: dict, size_margin_percent: float = 0.15) -> bool:
    """
    Checks (8):

    1. If the webapp don't have a wildcard DNS, consider as valid
    2. If both return a redirect, consider as false-positive
    3. If both return 4xx/5xx, consider as false-positive
    4. If target return error but baseline not, consider as false-positive
    5. If both has same hash value, consider as false-positive
    6. Using a float of 0.15, if the body response is less than it, consider as false-positive (avoid cookies, timestamps, etc)
    7. Target returns 403 but baseline returns 404, consider as vlaid to avoid skipping S3 buckets, Azure Blobs with no public access
    8. Redirect-based detection (Target redirects but baseline errors), consider as valid to avoid S3 wrong region
    
    Need to test more agains't others third-party services to detect false-positives or not detecting valid services
    """

    if result.get("no_wildcard"):
        return True

    baseline = result["baseline"]
    target = result["result"]

    baseline_status = baseline["status_code"]
    target_status = target["status_code"]

    baseline_is_redirect = 300 <= baseline_status < 400
    target_is_redirect = 300 <= target_status < 400
    if baseline_is_redirect and target_is_redirect:
        return False

    baseline_is_error = 400 <= baseline_status < 600
    target_is_error = 400 <= target_status < 600

    if target_status == 403 and baseline_status == 404:
        return True

    if baseline_is_error and target_is_error:
        return False
    
    if target_is_redirect and baseline_is_error:
        return False

    if (target_is_error or target_is_redirect) and not (baseline_is_error or baseline_is_redirect):
        return False

    target_is_success = 200 <= target_status < 300
    if target_is_success and baseline_is_error:
        return True

    if target["body_hash"] == baseline["body_hash"]:
        return False

    baseline_size = baseline["body_size"]
    target_size = target["body_size"]

    if baseline_size > 0:
        size_diff_percent = abs(target_size - baseline_size) / baseline_size
        if size_diff_percent < size_margin_percent:
            return False

    return True
    

async def run(target: str, output: str, threads: int, verbose: bool, services: list[str] | None = None, follow_redirects: bool = False) -> None:
    console.print("[cyan]saasy 0.1.2 :: discover third-party services from companies[/]\n", highlight=False)

    all_services = parse_services_yaml()

    if not all_services:
        return

    if services:
        all_services = [s for s in all_services if s["name"] in services]
        if not all_services:
            console.print("[red][!][/] No matching services found", highlight=False)
            return

    expanded_services = []
    for service in all_services:
        expanded_services.extend(expand_service(service))

    console.print(f"[yellow][!][/] Running... ({len(expanded_services)} checks)\n", highlight=False)

    semaphore = asyncio.Semaphore(threads)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=follow_redirects) as client:
        tasks = [
            check_service(client, service, target, semaphore, verbose)
            for service in expanded_services
        ]
        results = await asyncio.gather(*tasks)

    valid_findings = []
    for result in results:
        if result and compare_baseline(result):
            valid_findings.append(result)
            console.print(f"[bold green][+][/] {result['url']}", highlight=False)

    if not valid_findings:
        console.print("[yellow][-][/] No valid findings", highlight=False)
        return

    else:
        if output:
            with open(output, "w", encoding="utf-8") as output_file:
                for finding in valid_findings:
                    output_file.write(finding["url"] + "\n")

        console.print(f"\n[bold green][+][/] Found {len(valid_findings)} valid target(s)", highlight=False)