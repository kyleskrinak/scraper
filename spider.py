import os
import requests
import logging
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag

def read_domain_list(filename):
    # Read a list of domains from the provided file and return it as a list
    with open(filename, "r") as f:
        domain_list = [line.strip() for line in f.readlines() if line.strip()]
    return domain_list

def check_domains_status(domain_list, output_log_file):
    # Check the status of each domain in the domain list
    domains_to_remove = []
    successful_domains = []
    problematic_domains = []

    for domain in domain_list:
        try:
            # Attempt to make a request to the domain
            print(f"Checking domain: {domain}")
            response = requests.get(domain, timeout=10)  # Set a timeout for the request (e.g., 10 seconds)
            response.raise_for_status()  # Raise an exception if the status code indicates an error
            successful_domains.append(domain)
        except requests.exceptions.Timeout as e:
            # Handle timeout errors
            print(f"Timeout occurred for domain {domain}. Removing from the domain list.")
            logging.warning(f"Timeout occurred for domain {domain}. Removing from the domain list.")
            problematic_domains.append(domain)
            domains_to_remove.append(domain)
        except requests.exceptions.RequestException as e:
            # Handle other request errors
            print(f"An error occurred for domain {domain}: {e}. Removing from the domain list.")
            logging.error(f"An error occurred for domain {domain}: {e}. Removing from the domain list.")
            problematic_domains.append(domain)
            domains_to_remove.append(domain)

    for domain in domains_to_remove:
        domain_list.remove(domain)

    if problematic_domains:
        # If there are problematic domains, log them in the output log file
        with open(output_log_file, "w", encoding="utf-8") as f:
            f.write("Problematic domains (failed to return 200 or encountered errors):\n")
            for domain in problematic_domains:
                f.write(domain + "\n")

    return len(domain_list) > 0

def save_html(html_content, output_dir, url, downloaded_domains_list, total_domains):
    # Save the HTML content to a file with a corresponding filename based on the URL
    parsed_url = urlparse(url)
    domain_dir = os.path.join(output_dir, parsed_url.netloc)
    os.makedirs(domain_dir, exist_ok=True)  # Create the directory if it doesn't exist

    path = parsed_url.path or "/"
    if path == "/":
        filename = os.path.join(domain_dir, "index.html")
    else:
        filename = os.path.join(domain_dir, path[1:].replace("/", "_") + ".html")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

    downloaded_domains_list[0] += 1
    logging.info(f"{parsed_url.netloc}{path} - Downloaded")

def spider_website(url, output_dir):
    try:
        subprocess.run(["httrack", url, "-O", output_dir, "-%v", "--quiet", "-r20", "-X0", "-*.png", "-*.mp3", "-*.mp4", "-*.mov", "-*.css", "-*.js", "-*.pdf", "-*.zip", "-*.svg"])
        print(f"Spidering completed for {url}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while spidering {url}: {e}")

def spider_domains(domain_list, output_base_dir, output_log_file):
    total_domains = len(domain_list),
    downloaded_domains_list = [0]

    if not check_domains_status(domain_list, output_log_file):
        print("No valid domains found or all domains are problematic. Stopping execution.")
        logging.error("No valid domains found or all domains are problematic. Stopping execution.")
        exit()

    for domain in domain_list:
        parsed_domain = urlparse(domain)
        root_domain = parsed_domain.netloc
        print(f"Spidering domain: {domain}")
        logging.info(f"Spidering domain: {domain}")
        external_urls = set()
        visited_urls = set()
        spider_website(domain, output_base_dir)  # Removed max_depth argument here
        downloaded_domains_list[0] += 1
        print()

    if external_urls:
        with open(output_log_file, "a", encoding="utf-8") as f:
            f.write("External URLs found:\n")
            for url in external_urls:
                f.write(url + "\n")

if __name__ == "__main__":
    domain_list_filename = "domain_list.txt"
    domain_list = read_domain_list(domain_list_filename)

    output_base_directory = "downloaded_html"  # Base directory for all domain-specific output
    output_log_file = "spider_log.txt"  # Log file for spidering information

    # Initialize logging configuration
    logging.basicConfig(
        level=logging.INFO,
        filename=output_log_file,
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    spider_domains(domain_list, output_base_directory, output_log_file)