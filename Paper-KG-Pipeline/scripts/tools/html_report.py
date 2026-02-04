from pathlib import Path


def generate_html_report(
    result_dir: Path,
    report_name: str = "report",
    final_story_path: str = "./final_story.json",
    novelty_report_path: str = "./novelty_report.json",
) -> Path:
    if not isinstance(result_dir, Path):
        result_dir = Path(result_dir)
    final_story_path = final_story_path or "./final_story.json"
    novelty_report_path = novelty_report_path or "./novelty_report.json"
    html_template = (
        r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Idea2Story Visualization Report</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        [v-cloak] { display: none; }
        .fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
        .fade-enter-from, .fade-leave-to { opacity: 0; }
        .prose h3 { color: #1e3a8a; margin-top: 1.5em; font-weight: 600; }
        .prose p { margin-bottom: 1em; line-height: 1.6; }
    </style>
</head>
<body class="bg-slate-50 text-slate-800 min-h-screen">
    <div id="app" v-cloak class="container mx-auto px-4 py-8 max-w-6xl">
        
        <!-- Header -->
        <header class="mb-8 flex justify-between items-center border-b pb-4 border-slate-200">
            <div>
                <h1 class="text-3xl font-bold text-slate-900 tracking-tight">Idea2Story Report</h1>
                <p class="text-slate-500 mt-1">Research Logic & Novelty Analysis</p>
            </div>
            <div class="flex space-x-2">
                <button @click="activeTab = 'story'" 
                    :class="['px-4 py-2 rounded-lg font-medium transition-colors', activeTab === 'story' ? 'bg-blue-600 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-slate-100']">
                    <i class="fas fa-book-open mr-2"></i>Story Logic
                </button>
                <button @click="activeTab = 'novelty'" 
                    :class="['px-4 py-2 rounded-lg font-medium transition-colors', activeTab === 'novelty' ? 'bg-purple-600 text-white shadow-md' : 'bg-white text-slate-600 hover:bg-slate-100']">
                    <i class="fas fa-search mr-2"></i>Novelty Report
                </button>
            </div>
        </header>

        <!-- Loading / Upload State -->
        <div v-if="!dataLoaded" class="bg-white rounded-xl shadow-lg p-12 text-center border border-slate-200">
            <div v-if="loading" class="animate-pulse">
                <i class="fas fa-circle-notch fa-spin text-4xl text-blue-500 mb-4"></i>
                <p class="text-lg text-slate-600">Attempting to load data files...</p>
            </div>
            
            <div v-else class="space-y-6">
                <div class="text-amber-600 text-5xl mb-4"><i class="fas fa-exclamation-triangle"></i></div>
                <h2 class="text-2xl font-bold text-slate-800">Cannot Auto-Load Data</h2>
                <p class="text-slate-600 max-w-2xl mx-auto">
                    Browsers block direct file access (CORS) when opening HTML files directly. <br>
                    To fix this, you have two options:
                </p>
                
                <div class="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto mt-8 text-left">
                    <!-- Option A -->
                    <div class="bg-slate-50 p-6 rounded-lg border border-slate-200 hover:border-blue-400 transition-colors">
                        <h3 class="font-bold text-lg mb-2 text-blue-700">Option A: Start a Local Server (Recommended)</h3>
                        <p class="text-sm text-slate-600 mb-4">Run this command in the folder containing the files:</p>
                        <code class="block bg-slate-800 text-green-400 p-3 rounded mb-4 font-mono text-sm">python -m http.server 8000</code>
                        <p class="text-sm text-slate-600">Then open <a href="http://localhost:8000/report_visualization.html" class="text-blue-600 underline hover:text-blue-800">http://localhost:8000/report_visualization.html</a></p>
                    </div>

                    <!-- Option B -->
                    <div class="bg-slate-50 p-6 rounded-lg border border-slate-200 hover:border-purple-400 transition-colors">
                        <h3 class="font-bold text-lg mb-2 text-purple-700">Option B: Manually Select Files</h3>
                        <p class="text-sm text-slate-600 mb-4">Select the JSON files from your computer:</p>
                        
                        <div class="space-y-3">
                            <div>
                                <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Select final_story</label>
                                <input type="file" accept=".json" @change="loadStoryFile" class="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"/>
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Select novelty_report</label>
                                <input type="file" accept=".json" @change="loadNoveltyFile" class="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-purple-50 file:text-purple-700 hover:file:bg-purple-100"/>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content -->
        <main v-if="dataLoaded">
            
            <!-- STORY TAB -->
            <transition name="fade" mode="out-in">
                <div v-if="activeTab === 'story'" key="story" class="bg-white rounded-xl shadow-lg border border-slate-200 overflow-hidden">
                    <div class="p-8 border-b border-slate-100 bg-gradient-to-r from-blue-50 to-white">
                        <h2 class="text-3xl font-extrabold text-slate-900 mb-4 leading-tight">{{ story.title }}</h2>
                        <div class="bg-white p-6 rounded-lg border-l-4 border-blue-500 shadow-sm italic text-slate-700">
                            <span class="font-bold text-blue-900 not-italic block mb-2 text-sm uppercase tracking-wide">Abstract</span>
                            {{ story.abstract }}
                        </div>
                    </div>

                    <div class="p-8 grid gap-8">
                        <div class="grid md:grid-cols-3 gap-6">
                            <div class="bg-red-50 p-6 rounded-lg border border-red-100">
                                <h3 class="text-red-800 font-bold mb-2 flex items-center"><i class="fas fa-exclamation-circle mr-2"></i>Problem Framing</h3>
                                <p class="text-sm text-red-900/80">{{ story.problem_framing }}</p>
                            </div>
                            <div class="bg-amber-50 p-6 rounded-lg border border-amber-100">
                                <h3 class="text-amber-800 font-bold mb-2 flex items-center"><i class="fas fa-random mr-2"></i>Gap & Pattern</h3>
                                <p class="text-sm text-amber-900/80">{{ story.gap_pattern }}</p>
                            </div>
                            <div class="bg-green-50 p-6 rounded-lg border border-green-100">
                                <h3 class="text-green-800 font-bold mb-2 flex items-center"><i class="fas fa-check-circle mr-2"></i>Solution</h3>
                                <p class="text-sm text-green-900/80">{{ story.solution }}</p>
                            </div>
                        </div>

                        <div class="grid md:grid-cols-2 gap-8">
                            <div>
                                <h3 class="text-xl font-bold text-slate-800 mb-4 border-b pb-2">Method Skeleton</h3>
                                <div class="space-y-3">
                                    <div v-for="(step, index) in parseSteps(story.method_skeleton)" :key="index" class="flex items-start">
                                        <div class="bg-blue-100 text-blue-700 font-bold rounded-full w-6 h-6 flex items-center justify-center flex-shrink-0 mt-1 mr-3 text-sm">{{ index + 1 }}</div>
                                        <p class="text-slate-700 bg-slate-50 p-3 rounded w-full">{{ step }}</p>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 class="text-xl font-bold text-slate-800 mb-4 border-b pb-2">Innovation Claims</h3>
                                <ul class="space-y-3">
                                    <li v-for="(claim, idx) in story.innovation_claims" :key="idx" class="flex items-start bg-purple-50 p-3 rounded border border-purple-100">
                                        <i class="fas fa-star text-purple-500 mt-1 mr-3"></i>
                                        <span class="text-purple-900 text-sm">{{ claim }}</span>
                                    </li>
                                </ul>
                            </div>
                        </div>

                        <div class="bg-slate-50 p-6 rounded-lg border border-slate-200">
                            <h3 class="text-lg font-bold text-slate-800 mb-2">Experimental Plan</h3>
                            <p class="text-slate-700">{{ story.experiments_plan }}</p>
                        </div>
                    </div>
                </div>

                <!-- NOVELTY TAB -->
                <div v-else-if="activeTab === 'novelty'" key="novelty" class="space-y-6">
                    <!-- Dashboard Cards -->
                    <div class="grid md:grid-cols-3 gap-6">
                        <div class="bg-white p-6 rounded-xl shadow-md border border-slate-200">
                            <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Analysis Risk Level</h3>
                            <div class="flex items-center">
                                <span :class="['px-3 py-1 rounded-full text-sm font-bold uppercase', getRiskColor(novelty.risk_level)]">
                                    {{ novelty.risk_level }}
                                </span>
                            </div>
                        </div>
                        <div class="bg-white p-6 rounded-xl shadow-md border border-slate-200">
                            <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Max Similarity</h3>
                            <div class="flex items-center">
                                <div class="text-3xl font-bold text-slate-800 mr-3">{{ (novelty.max_similarity * 100).toFixed(1) }}%</div>
                                <div class="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                                    <div class="h-full rounded-full transition-all duration-500" 
                                        :class="novelty.max_similarity > 0.8 ? 'bg-red-500' : (novelty.max_similarity > 0.5 ? 'bg-amber-500' : 'bg-green-500')"
                                        :style="{ width: (novelty.max_similarity * 100) + '%' }"></div>
                                </div>
                            </div>
                        </div>
                        <div class="bg-white p-6 rounded-xl shadow-md border border-slate-200">
                            <h3 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Embedding Model</h3>
                            <p class="text-sm font-mono text-slate-600 truncate" :title="novelty.embedding_model">{{ novelty.embedding_model }}</p>
                            <p class="text-xs text-slate-400 mt-1">Top K: {{ novelty.top_k }}</p>
                        </div>
                    </div>

                    <!-- User Idea -->
                    <div class="bg-white p-6 rounded-xl shadow-md border border-slate-200">
                        <h3 class="text-sm font-bold text-slate-500 uppercase mb-3">Original User Idea</h3>
                        <p class="text-lg text-slate-800 bg-slate-50 p-4 rounded-lg border border-slate-100">"{{ novelty.user_idea }}"</p>
                    </div>

                    <!-- Candidates List -->
                    <div class="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden">
                        <div class="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50">
                            <h3 class="font-bold text-slate-700">Similar Papers Discovered</h3>
                            <span class="text-xs bg-slate-200 text-slate-600 px-2 py-1 rounded-full">{{ novelty.candidates.length }} papers</span>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="w-full text-left text-sm">
                                <thead class="bg-slate-50 text-slate-500 font-semibold uppercase text-xs">
                                    <tr>
                                        <th class="px-6 py-3">Similarity</th>
                                        <th class="px-6 py-3">Title</th>
                                        <th class="px-6 py-3">Domain</th>
                                        <th class="px-6 py-3">Action</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-100">
                                    <tr v-for="paper in novelty.candidates" :key="paper.paper_id" class="hover:bg-slate-50 transition-colors">
                                        <td class="px-6 py-4 font-mono font-medium" :class="paper.cosine > 0.8 ? 'text-red-600' : 'text-slate-600'">
                                            {{ (paper.cosine * 100).toFixed(1) }}%
                                        </td>
                                        <td class="px-6 py-4 font-medium text-slate-900">{{ paper.title }}</td>
                                        <td class="px-6 py-4 text-slate-500">{{ paper.domain }}</td>
                                        <td class="px-6 py-4">
                                            <a :href="'https://openreview.net/forum?id=' + paper.paper_id" target="_blank" class="text-blue-600 hover:text-blue-800 hover:underline flex items-center">
                                                View <i class="fas fa-external-link-alt ml-1 text-xs"></i>
                                            </a>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </transition>

        </main>
        
        <footer class="mt-12 text-center text-slate-400 text-sm pb-8">
            <p>Generated by Idea2Paper • Run ID: {{ novelty?.run_id || 'Unknown' }}</p>
        </footer>
    </div>

    <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    activeTab: 'story',
                    loading: true,
                    story: null,
                    novelty: null,
                    error: null
                }
            },
            computed: {
                dataLoaded() {
                    return this.story && this.novelty;
                }
            },
            methods: {
                async loadData() {
                    this.loading = true;
                    try {
                        // Try to fetch local files relative to HTML
                        const [storyRes, noveltyRes] = await Promise.all([
                            fetch('"""
        f"{final_story_path}"
        r"""'),
                            fetch('"""
        f"{novelty_report_path}"
        r"""')
                        ]);

                        if (!storyRes.ok || !noveltyRes.ok) throw new Error("File not found");

                        this.story = await storyRes.json();
                        this.novelty = await noveltyRes.json();
                        this.loading = false;
                    } catch (e) {
                        console.warn("Auto-fetch failed (likely CORS or file missing). Waiting for user input.");
                        this.loading = false;
                    }
                },
                loadStoryFile(event) {
                    this.readFile(event.target.files[0], (data) => this.story = data);
                },
                loadNoveltyFile(event) {
                    this.readFile(event.target.files[0], (data) => this.novelty = data);
                },
                readFile(file, callback) {
                    if (!file) return;
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        try {
                            callback(JSON.parse(e.target.result));
                        } catch (err) {
                            alert("Invalid JSON file");
                        }
                    };
                    reader.readAsText(file);
                },
                parseSteps(stepString) {
                    if (!stepString) return [];
                    // Split by "Step X:" or semicolon
                    return stepString.split(/Step \d+:/).filter(s => s.trim()).map(s => s.trim().replace(/^;/, '').trim());
                },
                getRiskColor(level) {
                    const map = {
                        'low': 'bg-green-100 text-green-700',
                        'medium': 'bg-amber-100 text-amber-700',
                        'high': 'bg-red-100 text-red-700'
                    };
                    return map[level?.toLowerCase()] || 'bg-slate-100 text-slate-700';
                }
            },
            mounted() {
                this.loadData();
            }
        }).mount('#app');
    </script>
</body>
</html>"""
    )
    html_report_path = result_dir / f"{report_name}.html"
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    return html_report_path


__all__ = ["generate_html_report"]
