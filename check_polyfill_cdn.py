import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import argparse
from colorama import Fore, Style, init
from tqdm import tqdm
import re

init(autoreset=True)

def load_urls(file_path):
    with open(file_path, 'r') as file:
        urls = [line.strip() for line in file.readlines()]
    return [normalize_url(url) for url in urls]

def normalize_url(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        return 'https://' + url
    return url

def check_polyfill_cdn(url, verbose):
    polyfill_pattern = re.compile(r'http[s]?://.*polyfill\.io/.*')
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            src = script.get('src')
            if src and polyfill_pattern.match(src):
                if verbose:
                    print(f"{Fore.GREEN}Polyfill found in {url}")
                return True
        return False
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"{Fore.RED}Error accessing {url}: {e}")
        return False

def get_links_on_page(url, domain, verbose):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()
        for a_tag in soup.find_all('a', href=True):
            link = urljoin(url, a_tag['href'])
            if urlparse(link).netloc == domain:
                links.add(link)
        return links
    except requests.exceptions.RequestException as e:
        if verbose:
            print(f"{Fore.RED}Error accessing {url}: {e}")
        return set()

def main():
    parser = argparse.ArgumentParser(description="Check URLs for polyfill CDN usage.")
    parser.add_argument('-u', '--url', help="Run a single URL from input.")
    parser.add_argument('-f', '--file', default='urls.txt', help="Specify a file containing URLs.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output.")

    args = parser.parse_args()

    if args.url:
        urls = [normalize_url(args.url)]
    else:
        urls = load_urls(args.file)

    total_urls = len(urls)
    with tqdm(total=total_urls, desc="Scanning URLs", unit="url") as pbar:
        for url in urls:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc

            if args.verbose:
                print(f"Checking {url}...")
            uses_polyfill = check_polyfill_cdn(url, args.verbose)
            if not args.verbose and uses_polyfill:
                print(f"{Fore.RED}{url} uses polyfill CDN")

            if not uses_polyfill:
                if args.verbose:
                    print(f"Crawling links on {url}...")
                links = get_links_on_page(url, domain, args.verbose)
                for link in links:
                    if args.verbose:
                        print(f"Checking {link}...")
                    uses_polyfill = check_polyfill_cdn(link, args.verbose)
                    if not args.verbose and uses_polyfill:
                        print(f"{Fore.RED}{link} uses polyfill CDN")
            pbar.update(1)

if __name__ == "__main__":
    main()
