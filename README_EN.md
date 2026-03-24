# Cevher Parallel Machine Scheduling Application

🌍 *[Türkçe README için tıklayın](README.md)*

This project is a PyQt6-based desktop application that uses the **Simulated Annealing** algorithm to optimize machine and job sequencing in a factory. Data is saved to a cloud-based Back4App database, and the results are visualized with an interactive Gantt Chart.

## 📌 Project Overview & Workflow
The main goal of this application is to minimize delays, setup efficiency losses, and machine idle times in complex production lines. The program operates through the following steps:
1. **Data Loading:** Job durations, order quantities, and machine setup times are parsed from Excel files.
2. **Optimization (Scheduling):** The Simulated Annealing algorithm iterates through thousands of job sequencing scenarios to find the sequence that minimizes the total completion time (Makespan / $C_{max}$) within seconds.
3. **Cloud Synchronization:** The best results and algorithm performance history are automatically uploaded to a cloud database (Back4App).
4. **Visual Reporting:** The resulting optimal production plan is presented to operators and planning engineers on a detailed, interactive timeline (Gantt Chart).

## 📖 The Story Behind the Application & Advanced Algorithm Structure
Real-world production environments are highly complex. Unlike classic scheduling problems, this project addresses the following challenges:
- **Machine Constraints:** Not every job can be processed on every machine.
- **Variable Parameters:** The system handles random incoming orders, varying cycle times, and sequence-dependent setup times between machines.

To solve this highly dynamic problem, we supported the **Simulated Annealing** algorithm with a sophisticated **Hyper-heuristic** approach:
- During the search for solutions, the algorithm utilizes **Swap, Insert, and Inverse** methods to generate neighborhood variations.
- A **Reward-Penalty Scoring** system is implemented: methods that yield better results (lower Makespan) are rewarded, while unsuccessful ones are penalized.
- These accumulated scores are dynamically uploaded to a **centralized cloud database (Back4App)**. The cloud infrastructure was chosen specifically so that **users across different factories or units can cumulatively train and benefit from the same core intelligence.** For future scheduling tasks, the algorithm retrieves these global average scores to mathematically favor the most successful methods for this problem domain. This essentially allows the system to leverage collective computing experience to "learn" and generate smarter scheduling plans over time.

## 🚀 Features

- **Simulated Annealing Algorithm**: Minimizes the total completion time (Makespan / $C_{max}$) by finding the optimal production sequence.
- **User-Friendly UI**: Process progress is shown without freezing the interface, using PyQt6 and QThread.
- **Data Visualization**: Through Matplotlib integration, the interactive Gantt Chart shows exactly which job will be produced on which machine, at what time, and for how long.
- **Cloud Database**: Solution results are backed up to the cloud using the Back4App (Parse) infrastructure.

## 📦 Installation and Execution

### 1. Install Requirements
Python must be installed on your computer to run this project. To install the libraries:
```bash
pip install pandas numpy matplotlib PyQt6 python-dotenv requests
```

### 2. Set Environment Variables (API)
You need API keys for the cloud (Back4App) database connection:
1. Rename the `.env.example` file in the project root directory to `.env`.
2. Paste your own Back4App `Application ID` and `REST API Key` information inside.

### 3. Start the Application
Make sure the data files (`A_Z.xlsx`, `K_M.xlsx`, `M_Z.xlsx`, etc.) are in the same folder. Then run the main application:
```bash
python app_github.py
```

## 🛠 Technologies Used
- **Python 3.12**
- **PyQt6**: Graphical User Interface (GUI)
- **Matplotlib**: Gantt chart and results plotting
- **Pandas & Numpy**: Excel reading and data processing
- **Simulated Annealing**: Optimization algorithm
- **Back4App (REST API)**: Data storage

## 🔒 Security Warnings
**IMPORTANT:** NEVER upload your `.env` file containing your real API keys to your GitHub profile. The `.gitignore` settings are already configured in this project to prevent this.
