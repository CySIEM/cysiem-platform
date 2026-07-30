class Team5Service:

    def ask_ai(self, question: str):
        q = question.lower().strip()

        if "cybersecurity" in q or "cyber security" in q:
            answer = (
                "Cybersecurity is the practice of protecting computers, "
                "networks, applications, and data from cyber threats such as "
                "malware, phishing, ransomware, and unauthorized access."
            )

        elif "sql injection" in q or "sql" in q:
            answer = (
                "SQL Injection is a cyberattack where malicious SQL queries "
                "are inserted into an application's input fields. "
                "Prevent it using parameterized queries, prepared statements, "
                "and proper input validation."
            )

        elif "xss" in q or "cross site scripting" in q:
            answer = (
                "Cross-Site Scripting (XSS) allows attackers to inject "
                "malicious JavaScript into web pages. "
                "Prevent it by escaping output, validating user input, "
                "and implementing Content Security Policy (CSP)."
            )

        elif "phishing" in q:
            answer = (
                "Phishing is a social engineering attack used to steal "
                "credentials through fake emails or websites. "
                "Prevent it with MFA, email filtering, and user awareness."
            )

        elif "malware" in q:
            answer = (
                "Malware is malicious software such as viruses, worms, "
                "trojans, spyware, and ransomware designed to damage "
                "systems or steal information."
            )

        elif "virus" in q:
            answer = (
                "A computer virus is malicious software that replicates "
                "itself and spreads to other files or systems."
            )

        elif "worm" in q:
            answer = (
                "A computer worm spreads automatically across networks "
                "without user interaction."
            )

        elif "trojan" in q:
            answer = (
                "A Trojan Horse disguises itself as legitimate software "
                "while secretly performing malicious activities."
            )

        elif "spyware" in q:
            answer = (
                "Spyware secretly collects user information and activities "
                "without their knowledge."
            )

        elif "ransomware" in q:
            answer = (
                "Ransomware encrypts files and demands payment. "
                "Prevent it by maintaining backups, patching systems, "
                "and using endpoint protection."
            )

        elif "ddos" in q or "dos attack" in q:
            answer = (
                "A Distributed Denial of Service (DDoS) attack floods "
                "a server with excessive traffic, making it unavailable "
                "to legitimate users."
            )

        elif "firewall" in q:
            answer = (
                "A firewall monitors and filters incoming and outgoing "
                "network traffic based on predefined security rules."
            )

        elif "vpn" in q:
            answer = (
                "A Virtual Private Network (VPN) encrypts internet traffic "
                "to provide secure communication over public networks."
            )

        elif "encryption" in q:
            answer = (
                "Encryption converts readable data into unreadable ciphertext "
                "using cryptographic algorithms to protect confidentiality."
            )

        elif "authentication" in q:
            answer = (
                "Authentication verifies the identity of a user before "
                "granting access to systems or applications."
            )

        elif "authorization" in q:
            answer = (
                "Authorization determines what resources an authenticated "
                "user is allowed to access."
            )

        elif "mfa" in q or "multi factor" in q:
            answer = (
                "Multi-Factor Authentication (MFA) improves security by "
                "requiring two or more verification methods."
            )

        elif "password" in q:
            answer = (
                "A strong password should contain uppercase and lowercase "
                "letters, numbers, special characters, and should not be "
                "reused across multiple accounts."
            )

        elif "network" in q:
            answer = (
                "A computer network is a group of connected devices that "
                "share information and resources using communication protocols."
            )

        elif "soc" in q:
            answer = (
                "A Security Operations Center (SOC) continuously monitors, "
                "detects, investigates, and responds to cybersecurity incidents."
            )

        elif "siem" in q:
            answer = (
                "SIEM (Security Information and Event Management) collects, "
                "correlates, and analyzes security logs to detect threats."
            )

        elif "incident response" in q:
            answer = (
                "Incident Response is the structured process of identifying, "
                "containing, eradicating, recovering from, and documenting "
                "security incidents."
            )

        elif "wazuh" in q:
            answer = (
                "Wazuh is an open-source security platform that provides "
                "SIEM, XDR, file integrity monitoring, vulnerability detection, "
                "and log analysis."
            )

        elif "linux" in q:
            answer = (
                "Linux is a secure open-source operating system widely used "
                "for servers, cloud computing, and cybersecurity."
            )

        elif "windows" in q:
            answer = (
                "Windows is Microsoft's operating system. Security best "
                "practices include regular updates, Microsoft Defender, "
                "BitLocker, and least-privilege access."
            )

        else:
            answer = (
                "Sorry, I don't have information about that topic yet. "
                "Please ask about cybersecurity topics such as SQL Injection, "
                "XSS, Malware, Phishing, SIEM, Firewall, VPN, Encryption, "
                "SOC, Wazuh, Authentication, MFA, Ransomware, or Incident Response."
            )

        return {
            "success": True,
            "question": question,
            "answer": answer
        }