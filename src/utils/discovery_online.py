#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PrinterReaper - Online Discovery Module
Discovers PJL-compatible printers exposed on the internet via Shodan and Censys APIs.

Author: PrinterReaper Team
License: MIT
"""

import os
import json
import csv
import time
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Set, Optional, Tuple
import re

try:
    import shodan
    SHODAN_AVAILABLE = True
except ImportError:
    SHODAN_AVAILABLE = False
    print("[!] Shodan module not installed. Run: pip install shodan")

try:
    from censys.search import CensysHosts
    CENSYS_AVAILABLE = True
except ImportError:
    CENSYS_AVAILABLE = False
    print("[!] Censys module not installed. Run: pip install censys")


class PrinterDatabase:
    """Manages the printer models database from pjl.dat"""
    
    def __init__(self, db_path: str = "src/core/db/pjl.dat"):
        self.db_path = db_path
        self.models = []
        self.brands = defaultdict(list)
        self.load_database()
    
    def load_database(self) -> None:
        """Load printer models from pjl.dat"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.models = [line.strip() for line in f if line.strip()]
            
            print(f"[+] Loaded {len(self.models)} printer models from database")
            self._categorize_by_brand()
        except FileNotFoundError:
            print(f"[!] Database file not found: {self.db_path}")
            raise
        except Exception as e:
            print(f"[!] Error loading database: {e}")
            raise
    
    def _categorize_by_brand(self) -> None:
        """Categorize printer models by brand"""
        brand_patterns = {
            'HP': r'(?i)^(HP |LaserJet|DesignJet|OfficeJet|DeskJet|Business Inkjet|Color LaserJet)',
            'Brother': r'(?i)^Brother',
            'Xerox': r'(?i)^Xerox|^Phaser|^WorkCentre|^DocuPrint|^DocuColor',
            'Ricoh': r'(?i)^Aficio|^Ricoh',
            'Kyocera': r'(?i)^Kyocera|^FS-|^KM-|^TASKalfa',
            'Lexmark': r'(?i)^Lexmark|^Optra',
            'Sharp': r'(?i)^Sharp|^AR-|^MX-',
            'Dell': r'(?i)^Dell',
            'Konica Minolta': r'(?i)^(KONICA MINOLTA|bizhub|magicolor)',
            'Toshiba': r'(?i)^TOSHIBA|^e-Studio',
            'Samsung': r'(?i)^Samsung|^ML-|^CLP|^CLX',
            'Epson': r'(?i)^EPSON|^EPL-|^AL-',
            'Canon': r'(?i)^Canon|^imageRunner|^LBP-',
            'Lenovo': r'(?i)^Lenovo',
            'OKI': r'(?i)^OKI|^OKIPAGE',
        }
        
        for model in self.models:
            categorized = False
            for brand, pattern in brand_patterns.items():
                if re.match(pattern, model):
                    self.brands[brand].append(model)
                    categorized = True
                    break
            
            if not categorized:
                self.brands['Other'].append(model)
        
        print(f"[+] Categorized into {len(self.brands)} brands")
        for brand, models in sorted(self.brands.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"    - {brand}: {len(models)} models")
    
    def get_search_queries(self, limit_per_brand: int = 5) -> List[Dict[str, str]]:
        """Generate optimized search queries for APIs"""
        queries = []
        
        # Generic PJL queries
        queries.append({
            'type': 'generic',
            'query': 'port:9100 "PJL"',
            'description': 'Generic PJL printers on port 9100'
        })
        
        queries.append({
            'type': 'generic',
            'query': '"PJL Ready" port:9100',
            'description': 'Printers with PJL Ready message'
        })
        
        # Brand-specific queries (most popular models)
        brand_queries = {
            'HP': ['HP LaserJet', 'Color LaserJet', 'DesignJet'],
            'Brother': ['Brother HL-', 'Brother MFC-', 'Brother DCP-'],
            'Xerox': ['Xerox Phaser', 'Xerox WorkCentre'],
            'Ricoh': ['Aficio MP', 'Aficio SP'],
            'Kyocera': ['Kyocera FS-', 'Kyocera TASKalfa'],
            'Lexmark': ['Lexmark MS', 'Lexmark MX', 'Lexmark CS'],
            'Sharp': ['Sharp MX-', 'Sharp AR-'],
            'Dell': ['Dell Laser'],
            'Konica Minolta': ['bizhub', 'magicolor'],
        }
        
        for brand, patterns in brand_queries.items():
            for pattern in patterns[:limit_per_brand]:
                queries.append({
                    'type': 'brand',
                    'brand': brand,
                    'query': f'"{pattern}" port:9100',
                    'description': f'{brand} - {pattern}'
                })
        
        # Popular specific models
        popular_models = [
            'HP LaserJet 4050', 'HP LaserJet 4250', 'HP LaserJet P3015',
            'Brother HL-5370DW', 'Xerox Phaser 6500DN', 'Lexmark MS810'
        ]
        
        for model in popular_models:
            queries.append({
                'type': 'specific',
                'query': f'"{model}" port:9100',
                'description': f'Specific model: {model}'
            })
        
        return queries


class ShodanDiscovery:
    """Handles Shodan API interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        if not SHODAN_AVAILABLE:
            raise ImportError("Shodan module not available")
        
        self.api_key = api_key or os.environ.get('SHODAN_API_KEY')
        if not self.api_key:
            raise ValueError("Shodan API key not provided. Set SHODAN_API_KEY environment variable.")
        
        self.api = shodan.Shodan(self.api_key)
        self.results = []
        self.total_found = 0
    
    def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """Search Shodan for devices matching query"""
        try:
            print(f"[*] Shodan: Searching for '{query}'...")
            results = self.api.search(query, limit=max_results)
            
            matches = results.get('matches', [])
            total = results.get('total', 0)
            
            print(f"[+] Shodan: Found {len(matches)} results (total available: {total})")
            
            parsed_results = []
            for match in matches:
                parsed_results.append({
                    'ip': match.get('ip_str', 'N/A'),
                    'port': match.get('port', 9100),
                    'hostnames': match.get('hostnames', []),
                    'org': match.get('org', 'Unknown'),
                    'country': match.get('location', {}).get('country_name', 'Unknown'),
                    'country_code': match.get('location', {}).get('country_code', 'N/A'),
                    'city': match.get('location', {}).get('city', 'Unknown'),
                    'banner': match.get('data', '')[:500],  # First 500 chars
                    'timestamp': match.get('timestamp', ''),
                    'product': match.get('product', 'Unknown'),
                    'version': match.get('version', 'Unknown'),
                    'source': 'shodan'
                })
            
            self.results.extend(parsed_results)
            self.total_found += len(parsed_results)
            
            return parsed_results
            
        except shodan.APIError as e:
            print(f"[!] Shodan API Error: {e}")
            return []
        except Exception as e:
            print(f"[!] Shodan Error: {e}")
            return []
    
    def get_api_info(self) -> Dict:
        """Get API plan information"""
        try:
            info = self.api.info()
            return {
                'plan': info.get('plan', 'unknown'),
                'query_credits': info.get('query_credits', 0),
                'scan_credits': info.get('scan_credits', 0),
                'usage_limits': info.get('usage_limits', {})
            }
        except Exception as e:
            print(f"[!] Error getting Shodan API info: {e}")
            return {}


class CensysDiscovery:
    """Handles Censys API interactions"""
    
    def __init__(self, api_id: Optional[str] = None, api_secret: Optional[str] = None):
        if not CENSYS_AVAILABLE:
            raise ImportError("Censys module not available")
        
        self.api_id = api_id or os.environ.get('CENSYS_API_ID')
        self.api_secret = api_secret or os.environ.get('CENSYS_API_SECRET')
        
        if not self.api_id or not self.api_secret:
            raise ValueError("Censys API credentials not provided. Set CENSYS_API_ID and CENSYS_API_SECRET.")
        
        self.api = CensysHosts(self.api_id, self.api_secret)
        self.results = []
        self.total_found = 0
    
    def search(self, query: str, max_results: int = 100) -> List[Dict]:
        """Search Censys for hosts matching query"""
        try:
            print(f"[*] Censys: Searching for '{query}'...")
            
            # Convert Shodan query to Censys query format
            censys_query = self._convert_query(query)
            
            results = []
            count = 0
            
            for page in self.api.search(censys_query, per_page=min(100, max_results), pages=-1):
                for host in page:
                    if count >= max_results:
                        break
                    
                    results.append({
                        'ip': host.get('ip', 'N/A'),
                        'port': 9100,  # Default PJL port
                        'hostnames': host.get('names', []),
                        'org': host.get('autonomous_system', {}).get('name', 'Unknown'),
                        'country': host.get('location', {}).get('country', 'Unknown'),
                        'country_code': host.get('location', {}).get('country_code', 'N/A'),
                        'city': host.get('location', {}).get('city', 'Unknown'),
                        'banner': str(host.get('services', [{}])[0] if host.get('services') else '')[:500],
                        'timestamp': host.get('last_updated_at', ''),
                        'product': 'Unknown',
                        'version': 'Unknown',
                        'source': 'censys'
                    })
                    count += 1
                
                if count >= max_results:
                    break
            
            print(f"[+] Censys: Found {len(results)} results")
            
            self.results.extend(results)
            self.total_found += len(results)
            
            return results
            
        except Exception as e:
            print(f"[!] Censys Error: {e}")
            return []
    
    def _convert_query(self, shodan_query: str) -> str:
        """Convert Shodan query format to Censys format"""
        # Simple conversion - can be enhanced
        query = shodan_query
        
        # Convert port:9100 to services.port: 9100
        query = re.sub(r'port:(\d+)', r'services.port: \1', query)
        
        # Convert quoted strings to services.banner search
        if '"' in query and 'port' in query:
            # Extract quoted string
            match = re.search(r'"([^"]+)"', query)
            if match:
                search_term = match.group(1)
                query = f'services.banner: "{search_term}" and services.port: 9100'
        
        return query
    
    def get_api_info(self) -> Dict:
        """Get API account information"""
        try:
            account = self.api.account()
            return {
                'quota': account.get('quota', {}),
                'email': account.get('email', 'unknown')
            }
        except Exception as e:
            print(f"[!] Error getting Censys API info: {e}")
            return {}


class OnlineDiscoveryManager:
    """Main manager for online printer discovery"""
    
    def __init__(self, db_path: str = "src/core/db/pjl.dat",
                 shodan_key: Optional[str] = None,
                 censys_id: Optional[str] = None,
                 censys_secret: Optional[str] = None):
        
        self.printer_db = PrinterDatabase(db_path)
        
        # Initialize Shodan
        self.shodan = None
        if shodan_key or os.environ.get('SHODAN_API_KEY'):
            try:
                self.shodan = ShodanDiscovery(shodan_key)
                print("[+] Shodan API initialized")
            except Exception as e:
                print(f"[!] Shodan initialization failed: {e}")
        
        # Initialize Censys
        self.censys = None
        if (censys_id or os.environ.get('CENSYS_API_ID')) and \
           (censys_secret or os.environ.get('CENSYS_API_SECRET')):
            try:
                self.censys = CensysDiscovery(censys_id, censys_secret)
                print("[+] Censys API initialized")
            except Exception as e:
                print(f"[!] Censys initialization failed: {e}")
        
        if not self.shodan and not self.censys:
            print("[!] WARNING: No API credentials provided. Discovery will not work.")
        
        self.all_results = []
        self.stats = defaultdict(int)
    
    def discover(self, max_results_per_query: int = 100, 
                 delay_between_queries: float = 1.0,
                 use_shodan: bool = True,
                 use_censys: bool = True) -> Dict:
        """
        Discover printers online using Shodan and/or Censys
        
        Args:
            max_results_per_query: Maximum results per query
            delay_between_queries: Delay between API calls (seconds)
            use_shodan: Use Shodan API
            use_censys: Use Censys API (fallback if Shodan fails)
        
        Returns:
            Dictionary with discovery statistics and results
        """
        print("\n" + "="*70)
        print("  PrinterReaper - Online Printer Discovery")
        print("="*70 + "\n")
        
        start_time = time.time()
        queries = self.printer_db.get_search_queries()
        
        print(f"[*] Generated {len(queries)} search queries")
        print(f"[*] Max results per query: {max_results_per_query}")
        print(f"[*] Delay between queries: {delay_between_queries}s\n")
        
        for idx, query_info in enumerate(queries, 1):
            print(f"\n[{idx}/{len(queries)}] Query: {query_info['description']}")
            print(f"    Search: {query_info['query']}")
            
            results = []
            
            # Try Shodan first
            if use_shodan and self.shodan:
                try:
                    results = self.shodan.search(query_info['query'], max_results_per_query)
                    if results:
                        print(f"    [+] Shodan found {len(results)} devices")
                except Exception as e:
                    print(f"    [!] Shodan failed: {e}")
            
            # Fallback to Censys if Shodan found nothing or failed
            if not results and use_censys and self.censys:
                try:
                    time.sleep(delay_between_queries)  # Rate limiting
                    results = self.censys.search(query_info['query'], max_results_per_query)
                    if results:
                        print(f"    [+] Censys found {len(results)} devices")
                except Exception as e:
                    print(f"    [!] Censys failed: {e}")
            
            if results:
                for result in results:
                    result['query_type'] = query_info['type']
                    result['query_description'] = query_info['description']
                
                self.all_results.extend(results)
                self._update_stats(results)
            
            # Rate limiting
            if idx < len(queries):
                time.sleep(delay_between_queries)
        
        elapsed_time = time.time() - start_time
        
        # Remove duplicates
        self.all_results = self._remove_duplicates(self.all_results)
        
        print("\n" + "="*70)
        print(f"[+] Discovery completed in {elapsed_time:.2f}s")
        print(f"[+] Total unique devices found: {len(self.all_results)}")
        print("="*70 + "\n")
        
        return self._generate_summary()
    
    def _remove_duplicates(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate IPs, keeping the most informative entry"""
        unique = {}
        for result in results:
            ip = result['ip']
            if ip not in unique or len(result['banner']) > len(unique[ip]['banner']):
                unique[ip] = result
        
        return list(unique.values())
    
    def _update_stats(self, results: List[Dict]) -> None:
        """Update discovery statistics"""
        for result in results:
            self.stats['total_devices'] += 1
            self.stats[f"source_{result['source']}"] += 1
            self.stats[f"country_{result['country']}"] += 1
    
    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        # Country distribution
        countries = defaultdict(int)
        sources = defaultdict(int)
        organizations = defaultdict(int)
        
        for result in self.all_results:
            countries[result['country']] += 1
            sources[result['source']] += 1
            organizations[result['org']] += 1
        
        summary = {
            'total_devices': len(self.all_results),
            'total_queries': len(self.printer_db.get_search_queries()),
            'countries': dict(sorted(countries.items(), key=lambda x: x[1], reverse=True)),
            'sources': dict(sources),
            'top_organizations': dict(sorted(organizations.items(), key=lambda x: x[1], reverse=True)[:20]),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def export_results(self, output_dir: str = "discovery_results") -> None:
        """Export results to multiple formats"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON export
        json_file = os.path.join(output_dir, f"discovery_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': self._generate_summary(),
                'results': self.all_results
            }, f, indent=2)
        print(f"[+] JSON exported to: {json_file}")
        
        # CSV export
        csv_file = os.path.join(output_dir, f"discovery_{timestamp}.csv")
        if self.all_results:
            keys = self.all_results[0].keys()
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.all_results)
            print(f"[+] CSV exported to: {csv_file}")
        
        # HTML report
        html_file = os.path.join(output_dir, f"discovery_{timestamp}.html")
        self._export_html(html_file)
        print(f"[+] HTML report exported to: {html_file}")
    
    def _export_html(self, filepath: str) -> None:
        """Generate HTML report"""
        summary = self._generate_summary()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>PrinterReaper - Discovery Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #4CAF50; color: white; padding: 20px; border-radius: 5px; text-align: center; }}
        .stat-card h3 {{ margin: 0; font-size: 2em; }}
        .stat-card p {{ margin: 5px 0 0 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .banner {{ font-family: monospace; font-size: 0.85em; max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🖨️ PrinterReaper - Online Discovery Report</h1>
        <p class="timestamp">Generated: {summary['timestamp']}</p>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{summary['total_devices']}</h3>
                <p>Devices Found</p>
            </div>
            <div class="stat-card">
                <h3>{len(summary['countries'])}</h3>
                <p>Countries</p>
            </div>
            <div class="stat-card">
                <h3>{summary['total_queries']}</h3>
                <p>Queries Executed</p>
            </div>
        </div>
        
        <h2>📊 Country Distribution</h2>
        <table>
            <tr><th>Country</th><th>Count</th><th>Percentage</th></tr>
"""
        
        for country, count in list(summary['countries'].items())[:20]:
            percentage = (count / summary['total_devices'] * 100) if summary['total_devices'] > 0 else 0
            html += f"            <tr><td>{country}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>\n"
        
        html += """        </table>
        
        <h2>🏢 Top Organizations</h2>
        <table>
            <tr><th>Organization</th><th>Count</th></tr>
"""
        
        for org, count in list(summary['top_organizations'].items())[:20]:
            html += f"            <tr><td>{org}</td><td>{count}</td></tr>\n"
        
        html += """        </table>
        
        <h2>🔍 Discovered Devices</h2>
        <table>
            <tr>
                <th>IP Address</th>
                <th>Country</th>
                <th>Organization</th>
                <th>Product</th>
                <th>Source</th>
            </tr>
"""
        
        for result in self.all_results[:100]:  # Limit to first 100 for performance
            html += f"""            <tr>
                <td>{result['ip']}</td>
                <td>{result['country']}</td>
                <td>{result['org'][:50]}</td>
                <td>{result['product']}</td>
                <td>{result['source']}</td>
            </tr>
"""
        
        html += """        </table>
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)


def main():
    """Main function for testing"""
    print("PrinterReaper - Online Discovery Module")
    print("="*70)
    
    manager = OnlineDiscoveryManager()
    
    # Run discovery
    summary = manager.discover(
        max_results_per_query=50,
        delay_between_queries=1.5,
        use_shodan=True,
        use_censys=True
    )
    
    # Print summary
    print("\n📊 Discovery Summary:")
    print(f"  Total devices: {summary['total_devices']}")
    print(f"  Countries: {len(summary['countries'])}")
    print(f"  Sources: {summary['sources']}")
    
    print("\n🌍 Top 10 Countries:")
    for country, count in list(summary['countries'].items())[:10]:
        print(f"  {country}: {count}")
    
    # Export results
    manager.export_results()
    
    print("\n[+] Discovery complete!")


if __name__ == "__main__":
    main()

