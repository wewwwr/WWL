import urllib.request

# Исходные списки для DIRECT (белый список)
urls = [
    "https://raw.githubusercontent.com/Master-Yoba/shadowrocket-rules/release/rules-geosite/geosite-ru-mobile-whitelist.list",
    "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/whitelist.txt"
]

# Ручные правила, которые нужно пустить НАПРЯМУЮ
combined_rules = [
    "DOMAIN-SUFFIX,yoomoney.ru",
    "DOMAIN-SUFFIX,tbank.ru",
    "DOMAIN-SUFFIX,oneme.ru",
    "DEST-PORT,25",
    "DEST-PORT,465",
    "DEST-PORT,587"
]

# СПИСОК ИСКЛЮЧЕНИЙ: домены, которые НЕ НАДО пускать напрямую
exclusions = {
    "another-domain.ru",
}

# Умная проверка на исключения (отсекает и сам домен, и все его поддомены)
def is_excluded(domain):
    for ex in exclusions:
        if domain == ex or domain.endswith('.' + ex):
            return True
    return False

print("Начинаю загрузку и обработку списков...")

# Разделяем домены и прочие правила
domain_set = set()
other_rules = set()

def process_rule(line):
    line = line.strip()
    # Игнорируем пустые строки и комментарии
    if not line or line.startswith('#') or line.startswith('//'):
        return
    
    # Разбиваем строку по запятым и убираем пробелы
    parts = [p.strip() for p in line.split(',')]
    
    # Сценарий 1: В строке просто домен (например "vk.com" или "*.vk.com")
    if len(parts) == 1:
        domain = parts[0].lower()
        if domain.startswith("*."):
            domain = domain[2:] # Очищаем от звездочек
        if not is_excluded(domain):
            domain_set.add(domain)
            
    # Сценарий 2: Строка с типом правила (например "DOMAIN,vk.com" или "IP-CIDR,...")
    elif len(parts) >= 2:
        rule_type = parts[0].upper()
        content = parts[1].lower()
        
        # Если это правило касается домена, вытаскиваем сам домен
        if rule_type in ("DOMAIN", "DOMAIN-SUFFIX"):
            if content.startswith("*."):
                content = content[2:]
            if not is_excluded(content):
                domain_set.add(content)
        else:
            # Технические правила (DEST-PORT, IP-CIDR, DOMAIN-KEYWORD) оставляем как есть
            # При этом сохраняем оригинальную строку
            other_rules.add(line)

# Обрабатываем ручные правила
for rule in combined_rules:
    process_rule(rule)

# Обрабатываем списки из сети
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

# --- БЛОК ОПТИМИЗАЦИИ ПОДДОМЕНОВ ---
print("Оптимизирую список доменов (удаляю избыточные поддомены)...")

# Сортируем домены по длине: от коротких (корневых) к длинным (поддоменам)
sorted_domains = sorted(list(domain_set), key=len)

optimized_domains = []
for domain in sorted_domains:
    # Проверяем, покрывается ли этот домен уже добавленным коротким корнем
    is_redundant = any(
        domain == root or domain.endswith('.' + root) 
        for root in optimized_domains
    )
    if not is_redundant:
        optimized_domains.append(domain)

# Собираем финальный массив: сначала отсортированные домены, затем порты/IP
final_rules = sorted([f"DOMAIN-SUFFIX,{d}" for d in optimized_domains]) + sorted(list(other_rules))

# Сохраняем итоговый белый список
output_filename = "my_custom_direct_list.list"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("# Auto-generated Shadowrocket Whitelist (DIRECT)\n")
    for rule in final_rules:
        f.write(f"{rule}\n")

print(f"Готово! Избыточные поддомены вырезаны с корнем.")
print(f"Всего уникальных правил после оптимизации: {len(final_rules)}")
