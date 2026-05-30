import urllib.request

# Исходные списки для DIRECT (белый список)
urls = [
    "https://raw.githubusercontent.com/Master-Yoba/shadowrocket-rules/release/rules-geosite/geosite-ru-mobile-whitelist.list",
    "https://raw.githubusercontent.com/hxehex/russia-mobile-internet-whitelist/main/whitelist.txt"
]

# Ручные правила, которые нужно пустить НАПРЯМУЮ (DIRECT)
combined_rules = {
    "DOMAIN-SUFFIX,yoomoney.ru",
    "DOMAIN-SUFFIX,tbank.ru",
    "DOMAIN-SUFFIX,oneme.ru",
    "DEST-PORT,25",
    "DEST-PORT,465",
    "DEST-PORT,587"
}

# СПИСОК ИСКЛЮЧЕНИЙ: домены, которые НЕ НАДО пускать напрямую
exclusions = {
    "another-domain.ru",
}

print("Начинаю загрузку и обработку белых списков...")

for url in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as response:
            content = response.read().decode('utf-8')
            for line in content.splitlines():
                line = line.strip()
                
                # Игнорируем пустые строки и комментарии
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                
                # Извлекаем чистый домен для сверки с исключениями
                clean_domain = line.split(',')[-1].strip() if ',' in line else line
                
                # Если домен в исключениях — пропускаем его
                if clean_domain in exclusions:
                    continue
                
                # Приводим к единому стандарту Shadowrocket без лишних пробелов
                if ',' not in line:
                    line = f"DOMAIN-SUFFIX,{line}"
                else:
                    parts = line.split(',', 1)
                    line = f"{parts[0].strip()},{parts[1].strip()}"
                    
                combined_rules.add(line)
        print(f"Успешно обработан: {url}")
    except Exception as e:
        print(f"Ошибка при загрузке {url}: {e}")

# --- БЛОК ОПТИМИЗАЦИИ ПОДДОМЕНОВ ---
print("Оптимизирую список доменов (удаляю избыточные поддомены)...")

domain_suffixes = []
other_rules = []

# Разделяем доменные правила и порты (DEST-PORT)
for rule in combined_rules:
    if rule.startswith("DOMAIN-SUFFIX,"):
        domain = rule.split(",", 1)[1].strip().lower()
        if domain:
            domain_suffixes.append(domain)
    else:
        other_rules.append(rule)

# Сортируем уникальные домены по длине строки (корневые пойдут первыми)
domain_suffixes = sorted(list(set(domain_suffixes)), key=len)

optimized_domains = []
for domain in domain_suffixes:
    # Проверяем, есть ли уже родительский домен в optimized_domains
    is_redundant = any(
        domain == root or domain.endswith('.' + root) 
        for root in optimized_domains
    )
    if not is_redundant:
        optimized_domains.append(domain)

# Собираем финальный массив правил: порты + оптимизированные DOMAIN-SUFFIX
final_rules = other_rules + [f"DOMAIN-SUFFIX,{d}" for d in optimized_domains]

# Сохраняем итоговый белый список
output_filename = "my_custom_direct_list.list"
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("# Auto-generated Shadowrocket Whitelist (DIRECT)\n")
    for rule in sorted(final_rules):
        f.write(f"{rule}\n")

print(f"Готово! Избыточные поддомены отфильтрованы.")
print(f"Всего правил после оптимизации: {len(final_rules)}")
