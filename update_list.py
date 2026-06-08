import urllib.request
import datetime

# Исходные списки для DIRECT (белый список)
urls = [
    "https://raw.githubusercontent.com/Master-Yoba/shadowrocket-rules/release/rules-geosite/geosite-ru-mobile-whitelist.list",
    "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/whitelist.txt",
    "https://raw.githubusercontent.com/nncat01/RCVPN-SR/refs/heads/release/rules-geosite/whitelist.list"
]

# Ручные правила
combined_rules = [
    "DOMAIN-SUFFIX,yoomoney.ru",
    "DOMAIN-SUFFIX,samokat.ru",
    "DOMAIN-SUFFIX,vkusvill.ru",
    "DOMAIN-SUFFIX,oneme.ru",
    "DEST-PORT,25",
    "DEST-PORT,465",
    "DEST-PORT,587",
    
    # === ЭКОСИСТЕМА Т-БАНК / TINKOFF ===
    "DOMAIN,tm.t-bank-app.ru",
    "DOMAIN-SUFFIX,cdn-tinkoff.ru",
    "DOMAIN-SUFFIX,t-access.ru",
    "DOMAIN-SUFFIX,t-bank-app.ru",
    "DOMAIN-SUFFIX,t-bank-app.su",
    "DOMAIN-SUFFIX,t-bank.by",
    "DOMAIN-SUFFIX,t-bank.ru",
    "DOMAIN-SUFFIX,t-calls.ru",
    "DOMAIN-SUFFIX,t-capital-funds.ru",
    "DOMAIN-SUFFIX,t-cpa.ru",
    "DOMAIN-SUFFIX,t-dengi.ru",
    "DOMAIN-SUFFIX,t-finance.group",
    "DOMAIN-SUFFIX,t-finance.ru",
    "DOMAIN-SUFFIX,t-human.ru",
    "DOMAIN-SUFFIX,t-investlab.ru",
    "DOMAIN-SUFFIX,t-j.ru",
    "DOMAIN-SUFFIX,t-ofp.ru",
    "DOMAIN-SUFFIX,t-pulse.ru",
    "DOMAIN-SUFFIX,t-static.ru",
    "DOMAIN-SUFFIX,t-stekovka.ru",
    "DOMAIN-SUFFIX,t-tech.dev",
    "DOMAIN-SUFFIX,t-tech.ru",
    "DOMAIN-SUFFIX,t-tech.team",
    "DOMAIN-SUFFIX,t-technologies.ru",
    "DOMAIN-SUFFIX,t-tolk.ru",
    "DOMAIN-SUFFIX,t.finance",
    "DOMAIN-SUFFIX,tb-esim.ru",
    "DOMAIN-SUFFIX,tbank-online.com",
    "DOMAIN-SUFFIX,tbank.ru",
    "DOMAIN-SUFFIX,tconf.ru",
    "DOMAIN-SUFFIX,tcsbank.ru",
    "DOMAIN-SUFFIX,tdev.by",
    "DOMAIN-SUFFIX,time-messenger.ru",
    "DOMAIN-SUFFIX,tinkoff-group.com",
    "DOMAIN-SUFFIX,tinkoff.ai",
    "DOMAIN-SUFFIX,tinkoff.ru",
    "DOMAIN-SUFFIX,tinkoffcapital.ru",
    "DOMAIN-SUFFIX,tinkoffinsurance.ru",
    "DOMAIN-SUFFIX,tinkoffinsurancefuture.ru",
    "DOMAIN-SUFFIX,tinkoffjournal.ru",
    "DOMAIN-SUFFIX,tinkoffmobile.com",
    "DOMAIN-SUFFIX,tinkoff.com",
    "DOMAIN-SUFFIX,tinkoff.aero",
    "DOMAIN-SUFFIX,tinkoff.travel",
    "DOMAIN-SUFFIX,tinkoff.mobi",
    "DOMAIN-SUFFIX,tinkov.com",
    "DOMAIN-SUFFIX,tinsurance.ru",
    "DOMAIN-SUFFIX,tinsurancefuture.ru",
    "DOMAIN-SUFFIX,tmiaf.ru"
]

# СПИСОК ИСКЛЮЧЕНИЙ
exclusions = {
    "another-domain.ru",
}

# Защита от неправильной обрезки двойных доменных зон
double_tlds = {
    "com.ru", "net.ru", "org.ru", "pp.ru", "msk.ru", "spb.ru", 
    "gov.ru", "edu.ru", "ac.ru", "mil.ru", "int.ru",
    "co.uk", "org.uk", "gov.uk", "ac.uk"
}

def get_base_domain(domain):
    """Принудительно обрезает любой поддомен до корневого домена (site.com)"""
    parts = domain.split('.')
    if len(parts) <= 2:
        return domain
    
    # Проверяем, не является ли окончание двойной зоной (например, .msk.ru)
    possible_tld = f"{parts[-2]}.{parts[-1]}"
    if possible_tld in double_tlds:
        if len(parts) >= 3:
            return f"{parts[-3]}.{parts[-2]}.{parts[-1]}" # Оставляем sub.msk.ru
        return domain
    
    # Во всех остальных случаях берем строго два последних слова (site.com)
    return f"{parts[-2]}.{parts[-1]}"

def is_excluded(domain):
    for ex in exclusions:
        if domain == ex or domain.endswith('.' + ex):
            return True
    return False

print("Начинаю загрузку и жесткую фильтрацию списков...")

domain_set = set()
other_rules = set()

def process_rule(line):
    line = line.strip()
    if not line or line.startswith('#') or line.startswith('//'):
        return
    
    parts = [p.strip() for p in line.split(',')]
    
    # Извлекаем домен в зависимости от формата правила
    extracted_domain = None
    
    if len(parts) == 1:
        extracted_domain = parts[0].lower()
    elif len(parts) >= 2:
        rule_type = parts[0].upper()
        content = parts[1].lower()
        if rule_type in ("DOMAIN", "DOMAIN-SUFFIX"):
            extracted_domain = content
        else:
            other_rules.add(line)
            return

    # Если нашли домен - очищаем от звездочек, обрезаем до корня и проверяем исключения
    if extracted_domain:
        if extracted_domain.startswith("*."):
            extracted_domain = extracted_domain[2:]
            
        if not is_excluded(extracted_domain):
            base_domain = get_base_domain(extracted_domain)
            domain_set.add(base_domain)

# Прогоняем ручные правила
for rule in combined_rules:
    process_rule(rule)

# Прогоняем сетевые списки
for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8')
            for line in content.splitlines():
                process_rule(line)
        print(f"Успешно обработан: {url}")
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")

# Дополнительная чистка: удаляем возможные хвосты
sorted_domains = sorted(list(domain_set), key=len)
optimized_domains = []

for domain in sorted_domains:
    is_redundant = any(
        domain == root or domain.endswith('.' + root) 
        for root in optimized_domains
    )
    if not is_redundant:
        optimized_domains.append(domain)

# Формируем итоговый список
final_rules = sorted([f"DOMAIN-SUFFIX,{d}" for d in optimized_domains]) + sorted(list(other_rules))

# Сохраняем в файл
output_filename = "my_custom_direct_list.list"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("# Auto-generated Shadowrocket Whitelist (DIRECT)\n")
    
    # Добавляем метку времени, чтобы GitHub Actions всегда видел изменения и делал коммит
    current_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    f.write(f"# Last updated: {current_time} UTC\n")
    
    for rule in final_rules:
        f.write(f"{rule}\n")

print("Готово! Все сайты схлопнуты до корневых доменов.")
