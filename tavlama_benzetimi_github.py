import pandas as pd
import random
import math
import os
from dotenv import load_dotenv
load_dotenv()
from matplotlib import rcParams
import matplotlib.pyplot as plt
import time
import requests

start_time = time.time()  


FILE_PATH = "data (3).xlsx"
# Excel'den 'Jobs' sayfasını oku
full_jobs_df = pd.read_excel(FILE_PATH, sheet_name='Jobs')

# İlk birkaç satırı kontrol edelim
print(full_jobs_df.head())

# Excel'den tüm işleri oku
full_jobs_df = pd.read_excel(FILE_PATH, sheet_name='Jobs')

# Process (dk) hesapla
full_jobs_df["Process (dk)"] = full_jobs_df["Çevrim Süreleri"] * full_jobs_df["Sipariş miktarları"]

# Sipariş miktarı sıfırdan büyük olan işleri filtrele (Jobs ID’leri korunur)
jobs_df = full_jobs_df[full_jobs_df["Sipariş miktarları"] > 0].reset_index(drop=True)

# Makine sütunlarını bulma fonksiyonu
def get_machines(df):
    return [col for col in df.columns if col.startswith("M")]

machines = get_machines(jobs_df)

# Gerekli sütunları al (İş numarası kaybolmaz)
jobs_df = jobs_df[["Jobs", "Çevrim Süreleri", "Sipariş miktarları", "Process (dk)", "Release"] + machines]

machines = [col for col in jobs_df.columns if col.startswith('M')]
if not machines:
    raise ValueError("Excel'de M1, M2,... şeklinde makine sütunları bulunamadı!")


# Öncelikli iş listesi (manuel olarak belirleyin)
priority_jobs = []  # Örnek: Job_3, Job_5 ve Job_7 öncelikli olsun
other_jobs = [job['Jobs'] for job in jobs_df.to_dict('records') if job['Jobs'] not in priority_jobs]


# Tavlama benzetimi için parametreler
blocked_machines = [ ]  
INITIAL_SETUP = 26.8   # İlk setup süresi
jobs_df = pd.read_excel(FILE_PATH, sheet_name='Jobs')
user_params = {
    "initial_temp": 1000,
    "final_temp": 1,
    "alpha": 0.9,
    "iterations": 10,
    "delta_hh": 1.0
}
# Setup Times sayfasını oku ve hem index hem sütun isimlerini string yap
setup_times_df = pd.read_excel(FILE_PATH, sheet_name='Setup Times')
setup_times_df.set_index(setup_times_df.columns[0], inplace=True)
#print(setup_times_df[10,)

def get_machines(jobs_df: pd.DataFrame):
    return [col for col in jobs_df.columns if col.startswith('M')]
machines = get_machines(jobs_df)

# Cmax'ı hesaplama fonksiyonu
def calculate_cmax(c_schedules):
    return max(info['release_time'] for info in c_schedules.values())

# Çözümü güncelleme fonksiyonu


heuristics = ['swap', 'insert', 'inverse']
heuristic_scores = {h: 1.0 for h in heuristics}  # Başlangıç puanları
heuristic_gains = {h: 0.0 for h in heuristics}   # Her heuristic'in g değeri
delta_hh = 1  # Adaptasyon hassasiyeti (Dhh)
def choose_heuristic(heuristic_scores):
    # %10 ihtimalle tamamen rastgele seç
    if random.random() < 0.1:
        return random.choice(list(heuristic_scores.keys()))
    
    # Rulet tekerleği (kalan %90)
    total = sum(heuristic_scores.values())
    r = random.uniform(0, total)
    upto = 0
    for h, score in heuristic_scores.items():
        upto += score
        if r <= upto:
            return h
    return random.choice(list(heuristic_scores.keys()))

# Başlangıç skorları (30-30-30)
heuristic_scores = {'swap': 0.33, 'insert': 0.33, 'inverse': 0.33}

def update_heuristic_score(heuristic_scores, heuristic_gains, heuristic, f_ini, f_new, delta_hh):
    # 1. Performans katsayısı (g)
    g = max(0, (f_ini - f_new) / f_ini )  

    # 2. Seçilen heuristic için gain güncelle
    heuristic_gains[heuristic] = g

    # 3. Adaptif güncelleme skorları
    a = heuristic_scores['swap']   + delta_hh * heuristic_gains['swap']
    b = heuristic_scores['insert'] + delta_hh * heuristic_gains['insert']
    c = heuristic_scores['inverse']+ delta_hh * heuristic_gains['inverse']

    total = a + b + c
  
    heuristic_scores['swap']    =  (a / total)
    heuristic_scores['insert']  =   (b / total)
    heuristic_scores['inverse'] =   (c / total)

     
        
def generate_new_solution(current_solution, heuristic_scores, priority_jobs=None, last_delta=None):
    if priority_jobs is None:
        priority_jobs = []
        
    heuristic = choose_heuristic(heuristic_scores)
    new_solution = current_solution.copy()
    
    # Öncelikli işlerin indekslerini bul
    priority_indices = [i for i, job in enumerate(current_solution) if job['Jobs'] in priority_jobs]
    
    if heuristic == 'swap':
        # Öncelikli işleri swap dışında tut
        available_indices = [i for i in range(len(current_solution)) if i not in priority_indices]
        if len(available_indices) >= 2:
            i, j = random.sample(available_indices, 2)
            new_solution[i], new_solution[j] = new_solution[j], new_solution[i]
            
    elif heuristic == 'insert':
        # Öncelikli işleri sabit tut
        available_indices = [i for i in range(len(current_solution)) if i not in priority_indices]
        if len(available_indices) >= 2:
            i, j = random.sample(available_indices, 2)
            if i < j:
                new_solution = new_solution[:i] + [new_solution[j]] + new_solution[i:j] + new_solution[j+1:]
            else:
                new_solution = new_solution[:j] + [new_solution[i]] + new_solution[j:i] + new_solution[i+1:]
                
    elif heuristic == 'inverse':
        # Öncelikli işleri içermeyen aralıkları seç
        available_indices = [i for i in range(len(current_solution)) if i not in priority_indices]
        if len(available_indices) >= 2:
            i, j = sorted(random.sample(available_indices, 2))
            new_solution = new_solution[:i] + new_solution[i:j+1][::-1] + new_solution[j+1:]
    
    return new_solution, heuristic


def generate_random_solution(jobs_df, priority_jobs=None):
    if priority_jobs is None:
        priority_jobs = []
    
    jobs_list = jobs_df.to_dict('records')
    
    # Öncelikli işleri belirtilen sırayla al
    priority = [job for job in jobs_list if job['Jobs'] in priority_jobs]
    # Öncelik sırasını koru: priority_jobs listesindeki sıraya göre
    priority = sorted(priority, key=lambda x: priority_jobs.index(x['Jobs']))
    
    # Diğer işleri rastgele karıştır
    others = [job for job in jobs_list if job['Jobs'] not in priority_jobs]
    random.shuffle(others)
    
    # Öncelikli işleri başa, diğerlerini sona ekle
    return priority + others
 
   
def neh_algorithm(jobs_df, machines, setup_times_df):
    # İşleri işlem sürelerine göre azalan sırayla sıralayın
    jobs_df_sorted = jobs_df.sort_values(by='Process (dk)', ascending=False)

    # İlk iş ile başla
    current_solution = [jobs_df_sorted.iloc[0]]

    # Diğer işleri sırayla ekleyin
    for i in range(1, len(jobs_df_sorted)):
        best_cmax = float('inf')
        best_solution = None

        # Yeni işin her pozisyonda denenmesi
        for position in range(len(current_solution) + 1):
            new_solution = current_solution[:position] + [jobs_df_sorted.iloc[i]] + current_solution[position:]
            c_schedules = create_schedule(new_solution, machines, setup_times_df)
            cmax = calculate_cmax(c_schedules)

            # Eğer bu çözüm daha iyi ise, en iyi çözümü güncelle
            if cmax < best_cmax:
                best_cmax = cmax
                best_solution = new_solution

        # En iyi çözümü geçerli çözüme ekleyin
        current_solution = best_solution

    return current_solution

# İş zamanlaması oluşturma fonksiyonu
def create_schedule(jobs_df, machines, setup_times_df, blocked_machines=None, priority_jobs=None):
    if blocked_machines is None:
        blocked_machines = []
    if priority_jobs is None:
        priority_jobs = []
    
    available_machines = [m for m in machines if m not in blocked_machines]
    c_schedules = {machine: {'schedule': [], 'release_time': 0, 'last_job': None} 
                  for machine in available_machines}

    # Öncelikli işler için kullanılacak makineleri tut
    used_machines_for_priority = set()

    # 1. ADIM: Öncelikli işleri TEK bir makinede ilk iş olarak ata
    for job in [j for j in jobs_df if j['Jobs'] in priority_jobs]:
        j_id = job['Jobs']
        p_time = job['Process (dk)']
        r_time = job['Release']
        
        # Bu işi işleyebilen ve henüz öncelikli iş atanmamış makineler
        capable_machines = [m for m in available_machines 
                          if (job[m] == 1) and (m not in used_machines_for_priority)]
        
        if not capable_machines:
            print(f"⚠️ Kritik Uyarı: Öncelikli Job_{j_id} için uygun makine kalmadı!")
            continue

        # En erken işi bitirebilecek makineyi seç
        selected_machine = None
        min_finish_time = float('inf')
        
        for m in capable_machines:
            setup_time = INITIAL_SETUP
            start_time = max(r_time, setup_time)
            finish_time = start_time + p_time
            
            if finish_time < min_finish_time:
                min_finish_time = finish_time
                selected_machine = m

        if selected_machine:
            c_schedules[selected_machine]['schedule'].append(j_id)
            c_schedules[selected_machine]['release_time'] = min_finish_time
            c_schedules[selected_machine]['last_job'] = j_id
            used_machines_for_priority.add(selected_machine)

    # 2. ADIM: Diğer işleri ata
    for job in [j for j in jobs_df if j['Jobs'] not in priority_jobs]:
        j_id = job['Jobs']
        p_time = job['Process (dk)']
        r_time = job['Release']
        
        capable_machines = [m for m in available_machines if job[m] == 1]
        
        if not capable_machines:
            print(f"⚠️ Uyarı: Job_{j_id} hiçbir makinede işlenemiyor! Atlanıyor...")
            continue

        # En erken tamamlanabilecek makineyi seç
        selected_machine = None
        min_finish_time = float('inf')

        for m in capable_machines:
            prev_release = c_schedules[m]['release_time']
            prev_job = c_schedules[m]['last_job']
            setup_time = setup_times_df.loc[f"Job_{prev_job}", f"Job_{j_id}"] if prev_job else INITIAL_SETUP
            start_time = max(prev_release + setup_time, r_time)
            finish_time = start_time + p_time

            if finish_time < min_finish_time:
                min_finish_time = finish_time
                selected_machine = m

        if selected_machine:
            c_schedules[selected_machine]['schedule'].append(j_id)
            c_schedules[selected_machine]['release_time'] = min_finish_time
            c_schedules[selected_machine]['last_job'] = j_id

    return c_schedules


def simulated_annealing(jobs_df, setup_times_df, machines, user_params,
                        blocked_machines=None, priority_jobs=None, stop_check=lambda: False):

    current_solution = generate_random_solution(jobs_df, priority_jobs)
    c_schedules = create_schedule(current_solution, machines, setup_times_df, blocked_machines, priority_jobs)
    current_cmax = calculate_cmax(c_schedules)
    best_solution, best_cmax, best_schedules = current_solution[:], current_cmax, c_schedules.copy()

    temp = user_params["initial_temp"]
    final_temp = user_params["final_temp"]
    alpha = user_params["alpha"]
    iterations = user_params["iterations"]
    delta_hh = user_params["delta_hh"]

    iteration_number = 0
    current_cmax_values = [current_cmax]
    best_cmax_values = [best_cmax]

    print(f"Iteration {iteration_number} Cmax: {int(best_cmax)}")

    heuristic_scores = {h: 1.0 for h in heuristics}
    heuristic_usage_count = {h: 0 for h in heuristics}

    while temp > final_temp:
        if stop_check():
            print("🛑 İşlem kullanıcı tarafından durduruldu.")
            break

        for _ in range(iterations):
            if stop_check():
                print("🛑 İşlem kullanıcı tarafından durduruldu.")
                break

            new_solution, used_heuristic = generate_new_solution(current_solution, heuristic_scores)
            heuristic_usage_count[used_heuristic] += 1

            new_schedules = create_schedule(new_solution, machines, setup_times_df, blocked_machines, priority_jobs)
            new_cmax = calculate_cmax(new_schedules)

            score_str = {h: f"{s:.3f}" for h, s in heuristic_scores.items()}
            print(f"I{iteration_number}, T: {temp:.1f}, heuristic: {used_heuristic}, Scores: {score_str}")

            accept = False
            if new_cmax < current_cmax:
                accept = True
            elif random.random() < math.exp((current_cmax - new_cmax) / temp):
                accept = True

            update_heuristic_score(heuristic_scores, heuristic_gains, used_heuristic, current_cmax, new_cmax, delta_hh)

            if accept:
                current_solution = new_solution
                current_cmax = new_cmax
                c_schedules = new_schedules

                if current_cmax < best_cmax:
                    best_solution = current_solution[:]
                    best_cmax = current_cmax
                    best_schedules = c_schedules.copy()

            current_cmax_values.append(current_cmax)
            best_cmax_values.append(best_cmax)

        temp *= alpha
        iteration_number += 1
        print(f"Iteration {iteration_number} Cmax: {int(best_cmax)}")

    print("\nHeuristic Kullanım Sayıları:")
    for h, count in heuristic_usage_count.items():
        print(f"  {h}: {count} kere kullanıldı")

    return best_solution, best_cmax, best_schedules, current_cmax_values, best_cmax_values, heuristic_scores



# Cmax Değerlerini Çizme Fonksiyonu
def plot_cmax_iterations(current_cmax_values, best_cmax_values):
    plt.figure(figsize=(10, 6))
    plt.plot(current_cmax_values, label="Current Cmax", color='r', linestyle='--')
    plt.plot(best_cmax_values, label="Best Cmax", color='b', linewidth=2)

    plt.xlabel('Iteration')
    plt.ylabel('Cmax')
    plt.title('Cmax vs Iteration')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()



def plot_gantt_chart_final(best_schedules, setup_times_df, jobs_df, initial_setup=26.8, cmax_value=None):
    from matplotlib.patches import Rectangle
    import matplotlib.patheffects as pe

    plt.style.use('default')
    rcParams.update({
        'axes.facecolor': '#F9F9F9',
        'grid.color': '#E0E0E0',
        'grid.linewidth': 1.8,
        'axes.grid': True,
        'axes.axisbelow': True,
        'font.family': 'DejaVu Sans',
        'font.size': 10,
    })

    num_machines = len(best_schedules)
    fig_height = max(8, num_machines * 0.45)
    fig, ax = plt.subplots(figsize=(18, fig_height))

    color_palette = [
        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
        '#1abc9c', '#d35400', '#34495e', '#16a085', '#c0392b',
        '#8e44ad', '#27ae60', '#e67e22', '#2980b9', '#c0392b'
    ] * 3

    setup_color = '#555555'
    highlight_color = '#e74c3c'

    title = "Üretim Planlama Gantt Şeması"
    if cmax_value is not None:
        cmax_int = int(round(cmax_value))
        title += f"\nToplam Süre: {cmax_int} dakika"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

    machine_height = 0.7
    spacing = 1.0
    bar_info = []  # Tooltip icin bilgi deposu

    max_time = 0
    for machine_idx, (machine, schedule_info) in enumerate(best_schedules.items()):
        schedule = schedule_info['schedule']
        last_job_end_time = 0
        y_pos = machine_idx * spacing

        for i, job_id in enumerate(schedule):
            job_row = jobs_df[jobs_df['Jobs'] == job_id].iloc[0]
            job_process_time = int(round(job_row['Process (dk)']))

            setup_time = int(round(initial_setup if i == 0 else setup_times_df.loc[f"Job_{schedule[i-1]}", f"Job_{job_id}"]))

            if setup_time > 0:
                setup_start = last_job_end_time
                ax.barh(y_pos, setup_time, left=setup_start,
                        color=setup_color, height=machine_height*0.5,
                        edgecolor='white', alpha=0.7, linewidth=0.3)

            job_start = last_job_end_time + setup_time
            job_end = job_start + job_process_time
            job_color = color_palette[job_id % len(color_palette)]

            bar = ax.barh(y_pos, job_process_time, left=job_start,
                    color=job_color, height=machine_height,
                    edgecolor='white', linewidth=1.0, alpha=0.9)

            # Tooltip icin bilgileri sakla
            bar_info.append({
                'x_start': job_start,
                'x_end': job_end,
                'y': y_pos,
                'height': machine_height,
                'job_id': job_id,
                'duration': job_process_time,
                'setup': setup_time,
                'machine': machine
            })

            # Cubuk icine yazi: max_time'a gore pixel basina ne kadar alan var hesapla
            bar_width_ratio = job_process_time / max(max_time, 1) if max_time > 0 else 0.1
            # Cubuk yeterince genisse is adi + süre yaz
            if job_process_time >= 800:
                label = f"J{job_id}\n{job_process_time}"
                ax.text(job_start + job_process_time / 2, y_pos, label,
                        va='center', ha='center', color='white',
                        fontsize=6.5, fontweight='bold',
                        path_effects=[pe.withStroke(linewidth=2, foreground='black')])
            elif job_process_time >= 300:
                ax.text(job_start + job_process_time / 2, y_pos, f"J{job_id}",
                        va='center', ha='center', color='white',
                        fontsize=6, fontweight='bold',
                        path_effects=[pe.withStroke(linewidth=2, foreground='black')])

            last_job_end_time = job_end
            if last_job_end_time > max_time:
                max_time = last_job_end_time

    # Eksen ayarlari
    ax.set_xlabel('Zaman (dakika)', fontsize=12, labelpad=10)
    ax.set_ylabel('Makineler', fontsize=12, labelpad=12)
    ax.set_yticks([i * spacing for i in range(num_machines)])
    ax.set_yticklabels([f"{m}" for m in best_schedules.keys()],
                      fontsize=9, fontweight='bold')

    ax.set_xlim(0, max_time * 1.08)
    if max_time > 20000:
        tick_step = 5000
    elif max_time > 10000:
        tick_step = 3000
    elif max_time > 5000:
        tick_step = 2000
    else:
        tick_step = 1000
    ax.set_xticks(range(0, int(max_time * 1.08) + tick_step, tick_step))
    ax.tick_params(axis='x', labelsize=9, rotation=45)

    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    for spine in ['bottom', 'left']:
        ax.spines[spine].set_color('#AAAAAA')
    ax.axvline(x=max_time, color=highlight_color, linestyle='--', linewidth=2)

    # Interaktif tooltip (fare ile uszerine gelince bilgi gosterir)
    annot = ax.annotate("", xy=(0,0), xytext=(15, 15),
                        textcoords="offset points",
                        bbox=dict(boxstyle="round,pad=0.4", fc="#222222", ec="#888888", alpha=0.95),
                        fontsize=10, color='white', fontweight='bold',
                        arrowprops=dict(arrowstyle="->", color="#888888"))
    annot.set_visible(False)

    def on_hover(event):
        if event.inaxes != ax:
            annot.set_visible(False)
            fig.canvas.draw_idle()
            return
        found = False
        for info in bar_info:
            if (info['x_start'] <= event.xdata <= info['x_end'] and
                info['y'] - info['height']/2 <= event.ydata <= info['y'] + info['height']/2):
                text = (f"İş: J{info['job_id']}\n"
                        f"Süre: {info['duration']} dk\n"
                        f"Başlangıç: {info['x_start']}\n"
                        f"Bitiş: {info['x_end']}\n"
                        f"Kurulum: {info['setup']} dk\n"
                        f"Makine: {info['machine']}")
                annot.xy = (event.xdata, event.ydata)
                annot.set_text(text)
                annot.set_visible(True)
                found = True
                break
        if not found:
            annot.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_hover)

    plt.tight_layout()
    return fig
 
def save_result_to_back4app(user_params, best_cmax, execution_time, heuristic_scores):
    headers = {
        "X-Parse-Application-Id": os.getenv("BACK4APP_APP_ID"),
        "X-Parse-REST-API-Key": os.getenv("BACK4APP_REST_API_KEY"),
        "Content-Type": "application/json"
    }

    data = {
        "initial_temp": user_params["initial_temp"],
        "final_temp": user_params["final_temp"],
        "alpha": user_params["alpha"],
        "iterations": user_params["iterations"],
        "delta_hh": user_params["delta_hh"],
        "Cmax": best_cmax,
        "runtime_sec": round(execution_time, 2),
        "swap_score": round(heuristic_scores.get("swap", 0.0), 4),
        "insert_score": round(heuristic_scores.get("insert", 0.0), 4),
        "inverse_score": round(heuristic_scores.get("inverse", 0.0), 4),
    }

    response = requests.post("https://parseapi.back4app.com/classes/cevher_sche",
                             headers=headers, json=data)

    if response.status_code == 201:
        print("✅ Veri başarıyla Back4App'e kaydedildi.")
    else:
        print(f"❌ Hata ({response.status_code}): {response.text}")


def fetch_and_print_heuristic_averages_all():
    url = "https://parseapi.back4app.com/classes/cevher_sche"
    headers = {
        "X-Parse-Application-Id": os.getenv("BACK4APP_APP_ID"),
        "X-Parse-REST-API-Key": os.getenv("BACK4APP_REST_API_KEY"),
    }

    limit = 100
    skip = 0
    all_records = []

    while True:
        params = {"limit": limit, "skip": skip, "order": "-createdAt"}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"❌ Veri çekme hatası: {response.status_code}")
            break

        records = response.json().get("results", [])
        if not records:
            break

        all_records.extend(records)
        if len(records) < limit:
            break
        skip += limit

    if not all_records:
        print("⚠️ Hiçbir kayıt alınamadı.")
        return

    total_swap = total_insert = total_inverse = 0.0
    valid_count = 0

    for record in all_records:
        try:
            total_swap += record["swap_score"]
            total_insert += record["insert_score"]
            total_inverse += record["inverse_score"]
            valid_count += 1
        except KeyError:
            continue

    if valid_count == 0:
        print("⚠️ Geçerli heuristic skorları içeren kayıt bulunamadı.")
        return

    avg_swap = total_swap / valid_count
    avg_insert = total_insert / valid_count
    avg_inverse = total_inverse / valid_count

    print("\n📈 Tüm Back4App Kayıtlarında Ortalama Heuristic Skorları:")
    print(f"🔄 Swap     Ortalaması: {avg_swap:.4f}")
    print(f"📥 Insert   Ortalaması: {avg_insert:.4f}")
    print(f"🔃 Inverse  Ortalaması: {avg_inverse:.4f}")
    print(f"📊 Toplam Kayıt Sayısı: {valid_count}")




def get_heuristic_averages_text():
    import requests

    url = "https://parseapi.back4app.com/classes/cevher_sche"
    headers = {
        "X-Parse-Application-Id": os.getenv("BACK4APP_APP_ID"),
        "X-Parse-REST-API-Key": os.getenv("BACK4APP_REST_API_KEY"),
    }

    limit = 100
    skip = 0
    all_records = []

    while True:
        params = {"limit": limit, "skip": skip, "order": "-createdAt"}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            return f"❌ Veri çekme hatası: {response.status_code}"

        records = response.json().get("results", [])
        if not records:
            break

        all_records.extend(records)
        if len(records) < limit:
            break
        skip += limit

    if not all_records:
        return "⚠️ Hiçbir kayıt alınamadı."

    total_swap = total_insert = total_inverse = 0.0
    valid_count = 0

    for record in all_records:
        try:
            total_swap += record["swap_score"]
            total_insert += record["insert_score"]
            total_inverse += record["inverse_score"]
            valid_count += 1
        except KeyError:
            continue

    if valid_count == 0:
        return "⚠️ Geçerli heuristic skorları içeren kayıt bulunamadı."

    avg_swap = total_swap / valid_count
    avg_insert = total_insert / valid_count
    avg_inverse = total_inverse / valid_count

    # Konsol için
    print("\n📈 Tüm Back4App Kayıtlarında Ortalama Heuristic Skorları:")
    print(f"🔄 Swap     Ortalaması: {avg_swap:.4f}")
    print(f"📥 Insert   Ortalaması: {avg_insert:.4f}")
    print(f"🔃 Inverse  Ortalaması: {avg_inverse:.4f}")
    print(f"📊 Toplam Kayıt Sayısı: {valid_count}")

    # GUI için dönen metin
    return (
        "📈 Tüm Back4App Kayıtlarında Ortalama Heuristic Skorları:\n"
        f"🔄 Swap     Ortalaması: {avg_swap:.4f}\n"
        f"📥 Insert   Ortalaması: {avg_insert:.4f}\n"
        f"🔃 Inverse  Ortalaması: {avg_inverse:.4f}\n"
        f"📊 Toplam Kayıt Sayısı: {valid_count}"
    )





if __name__ == "__main__":
    start_time = time.time()

    best_solution, best_cmax, best_schedules, current_cmax_values, best_cmax_values, heuristic_scores = simulated_annealing(
        jobs_df, setup_times_df, machines, user_params, blocked_machines, priority_jobs
    )

    # Cmax değerlerini çiz
    plot_cmax_iterations(current_cmax_values, best_cmax_values)
    cmax_value = calculate_cmax(best_schedules)
    plot_gantt_chart_final(best_schedules, setup_times_df, jobs_df, initial_setup=INITIAL_SETUP, cmax_value=cmax_value)

    execution_time = time.time() - start_time

    print(f"\n toplam çalışma süresi: {execution_time/60:.2f} dakika")

    print("\n📋 İş Atamaları (makine bazlı):\n")
    for machine, info in best_schedules.items():
        print(f"🔧 {machine}:")
        for idx, job_id in enumerate(info['schedule']):
            job_info = jobs_df[jobs_df['Jobs'] == job_id].iloc[0]
            order_qty = job_info['Sipariş miktarları']
            if order_qty > 0:
                print(f" Job_{job_id}, Sipariş: {int(order_qty)} adet, Süre: {int(job_info['Process (dk)'])} dk")
        print("-" * 40)

    print("\n📊 SON ITERASYONDAKİ HEURISTIC SKORLARI:")
    for h, s in heuristic_scores.items():
        print(f"🔸 {h.capitalize()} score: {s:.4f}")

    save_result_to_back4app(user_params, best_cmax, execution_time, heuristic_scores)
    fetch_and_print_heuristic_averages_all()


