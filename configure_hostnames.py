#!/usr/bin/env python3
"""
Hostname Configuration Helper for ETX Dashboard
This script helps configure the hostname mapping for login nodes (login01-10)
"""

import re

def configure_hostname_mapping():
    """Interactive configuration of hostname mapping"""
    print("🔧 ETX Dashboard Hostname Configuration")
    print("=" * 50)
    print()
    print("Your system is trying to connect to hostnames like 'login04' but they can't be resolved.")
    print("You need to configure the actual IP addresses for these login nodes.")
    print()
    
    # Get the current run_ETX.py content
    with open('run_ETX.py', 'r') as f:
        content = f.read()
    
    print("Please choose your configuration method:")
    print("1. Configure specific IP addresses for each login node")
    print("2. Use fully qualified domain names (FQDN)")
    print("3. Use a different hostname pattern")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == '1':
        configure_ip_mapping(content)
    elif choice == '2':
        configure_fqdn_mapping(content)
    elif choice == '3':
        configure_custom_pattern(content)
    else:
        print("Invalid choice. Exiting.")

def configure_ip_mapping(content):
    """Configure specific IP addresses for login nodes"""
    print("\n📍 Configuring IP Address Mapping")
    print("-" * 40)
    
    # Example IP configuration
    print("Example configuration:")
    print("login01 -> 202.20.185.101")
    print("login02 -> 202.20.185.102")
    print("login03 -> 202.20.185.103")
    print("login04 -> 202.20.185.104")
    print("etc...")
    print()
    
    base_ip = input("Enter the base IP address pattern (e.g., 202.20.185.10): ").strip()
    if not base_ip:
        print("No IP provided. Using default pattern.")
        base_ip = "202.20.185.10"
    
    # Generate the mapping
    mapping_lines = []
    for i in range(1, 11):
        hostname = f"login{i:02d}"
        ip = f"{base_ip[:-1]}{i}" if base_ip.endswith('0') else f"{base_ip}{i}"
        mapping_lines.append(f"        '{hostname}': '{ip}',")
    
    # Update the content
    updated_content = enable_ip_mapping(content, mapping_lines)
    
    # Write back to file
    with open('run_ETX.py', 'w') as f:
        f.write(updated_content)
    
    print(f"\n✅ Configuration updated!")
    print(f"Hostname mapping configured with base IP: {base_ip}")
    print("The system will now map:")
    for i in range(1, 11):
        hostname = f"login{i:02d}"
        ip = f"{base_ip[:-1]}{i}" if base_ip.endswith('0') else f"{base_ip}{i}"
        print(f"  {hostname} -> {ip}")

def configure_fqdn_mapping(content):
    """Configure FQDN mapping"""
    print("\n🌐 Configuring FQDN Mapping")
    print("-" * 40)
    
    domain = input("Enter your domain (e.g., hpc.university.edu): ").strip()
    if not domain:
        print("No domain provided. Exiting.")
        return
    
    # Update the content to use FQDN
    updated_content = enable_fqdn_mapping(content, domain)
    
    # Write back to file
    with open('run_ETX.py', 'w') as f:
        f.write(updated_content)
    
    print(f"\n✅ Configuration updated!")
    print(f"The system will now use FQDN with domain: {domain}")
    print("Examples:")
    print(f"  login01 -> login01.{domain}")
    print(f"  login04 -> login04.{domain}")

def enable_ip_mapping(content, mapping_lines):
    """Enable IP mapping in the content"""
    # Find the Method 2 section and uncomment it
    pattern = r'(# Method 2:.*?# hostname_mapping = \{)(.*?)(# \}.*?# print\(f"Mapping)'
    
    mapping_block = "\n".join(mapping_lines)
    replacement = f"\\1\n        hostname_mapping = {{\n{mapping_block}\n        }}\n        REMOTE_HOST = hostname_mapping.get(hostname, REMOTE_BASE_HOST)\n        \\3"
    
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also comment out Method 1 (direct hostname usage)
    updated_content = updated_content.replace(
        "REMOTE_HOST = hostname",
        "# REMOTE_HOST = hostname  # Commented out - using IP mapping instead"
    )
    
    return updated_content

def enable_fqdn_mapping(content, domain):
    """Enable FQDN mapping in the content"""
    # Find the Method 3 section and uncomment it
    pattern = r'# Method 3:.*?# REMOTE_HOST = f"\{hostname\}\.your-domain\.com"'
    replacement = f'# Method 3: Using FQDN with domain {domain}\n        REMOTE_HOST = f"{{hostname}}.{domain}"'
    
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also comment out Method 1 (direct hostname usage)
    updated_content = updated_content.replace(
        "REMOTE_HOST = hostname",
        "# REMOTE_HOST = hostname  # Commented out - using FQDN instead"
    )
    
    return updated_content

def configure_custom_pattern(content):
    """Configure custom hostname pattern"""
    print("\n🔧 Custom Hostname Pattern")
    print("-" * 40)
    print("This option allows you to define a custom pattern for hostname resolution.")
    print("You can modify the run_ETX.py file manually for advanced configurations.")
    print()
    
    pattern = input("Enter your hostname pattern (e.g., 'node-{hostname}' or leave blank): ").strip()
    
    if pattern:
        # Simple pattern replacement
        custom_mapping = f'REMOTE_HOST = "{pattern}".format(hostname=hostname)'
        updated_content = content.replace(
            "REMOTE_HOST = hostname",
            f"# REMOTE_HOST = hostname  # Using custom pattern\n        {custom_mapping}"
        )
        
        with open('run_ETX.py', 'w') as f:
            f.write(updated_content)
        
        print(f"\n✅ Configuration updated!")
        print(f"Using custom pattern: {pattern}")
    else:
        print("No pattern provided. Please edit run_ETX.py manually.")

if __name__ == "__main__":
    configure_hostname_mapping() 