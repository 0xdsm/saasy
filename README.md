<p align="center">
    <picture>
        <img src="img/cover.jpg">
    </picture>
</p>

<hr/>

saasy is a Python tool designed to enumerate third-party services from companies. It uses the targeted company name as the keyword and a placeholder scheme to create a service URL and see if it's a published service. To avoid false positives, it uses a comparison runtime mechanism based on status code, response body size, and response body hash (SHA-256) to generate a baseline and compare it with the actual request, analyzing if there is any similarity between the target service and the already known invalid baseline.

<br>

## Installation
We recommend using [pipx](https://github.com/pypa/pipx) to install the project, so you can run it from anywhere and make things easier.

### Linux
```
sudo apt install pipx git
pipx ensurepath
pipx install git+https://github.com/0xdsm/saasy
```

### MacOS
```
brew install pipx
pipx ensurepath
pipx install git+https://github.com/0xdsm/saasy
```

### Local
```
git clone https://github.com/0xdsm/saasy.git
pipx install .
```

### Updating
```
pipx reinstall saasy
```

<br>

## Usage

To start using saasy, you need to specify a target (keyword). The basic usage is as follows:

Basic usage:
```sh
saasy nubank
saasy 0.1.3 :: discover third-party services from companies

[!] Running... (299 checks)

[+] nubank.lightning.force.com
[+] nubank.onrender.com
[+] nubank.statuspage.io
[+] nubank.s3.us-east-1.amazonaws.com
[+] nubank.sharepoint.com
[+] hub.docker.com/u/nubank
[+] nubank.netlify.app
[+] nubank.pages.dev
[+] nubank.awsapps.com
[+] nubank.vercel.app
[+] nubank.zendesk.com
[+] nubank.wordpress.com
[+] nubank.auth0.com
[+] nubank.s3.amazonaws.com
[+] nubank.greenhouse.io
[+] nubank.monday.com
[+] nubank.storage.googleapis.com
[+] nubank.zoom.us
[+] nubank.surge.sh
[+] nubank.my.salesforce.com

[+] Found 20 valid target(s)
```

You can specify the flag `--verbose` to see the detailed enumeration process. For example:
```
saasy nubank --verbose
saasy 0.1.3 :: discover third-party services from companies

[!] Running... (299 checks)

[*] Capturing queue-core-windows baseline
[*] Capturing canny baseline
[*] Capturing onrender baseline
[*] Capturing s3-legacy-us-west-1 baseline
[*] Capturing s3-website-dot-eu-north-1 baseline
[*] azurecontainer-regional-australiaeast baseline failed (no wildcard DNS): [Errno 8] nodename nor servname provided, or not known
[*] fastly baseline failed (no wildcard DNS): [Errno 8] nodename nor servname provided, or not known
[*] acquia-env-qas baseline failed (no wildcard DNS): [Errno 8] nodename nor servname provided, or not known
[*] lightning-force target: {'status_code': 302, 'body_size': 0, 'body_hash': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', 'location': 'https://*.my.salesforce.com/'}
[*] Capturing railway baseline
[+] nubank.lightning.force.com
[*] onrender baseline: {'status_code': 404, 'body_size': 10, 'body_hash': '7515bf959b73b956ceb967351c7e299cbb3668a53d35f9c770eb72e00d93ced6', 'location': ''}
[*] twil baseline: {'status_code': 404, 'body_size': 9, 'body_hash': '0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5', 'location': ''}
```

Also, you can save the valid findings in a file with the flag `--output <filename>`. For example:
```
saasy nubank --output results.txt
```

<br>

## Flowchart
<picture>
    <img src="img/mermaid.png" height="1000px">
</picture>
<br>