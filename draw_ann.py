import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(14, 8))
ax.axis('off')

layer_info = [
    {"name": "Input Layer", "nodes": 6, "label": "6 Fitur Input", "details": ['Nama Blok', 'Luas Bangunan', 'Luas Tanah', 'Jumlah Kamar Tidur', 'Jumlah Kamar Mandi', 'Smart Door Lock']},
    {"name": "Hidden Layer 1", "nodes": 8, "label": "64 Neuron\n(Aktivasi: ReLU)", "details": []},
    {"name": "Hidden Layer 2", "nodes": 6, "label": "32 Neuron\n(Aktivasi: ReLU)", "details": []},
    {"name": "Hidden Layer 3", "nodes": 4, "label": "16 Neuron\n(Aktivasi: ReLU)", "details": []},
    {"name": "Output Layer", "nodes": 1, "label": "1 Neuron\n(Linear)", "details": ['Harga KPR\n(Prediksi)']}
]

left, right, bottom, top = 0.15, 0.85, 0.22, 0.85
n_layers = len(layer_info)
h_spacing = (right - left) / float(n_layers - 1)
v_spacing = (top - bottom) / float(max([layer["nodes"] for layer in layer_info]))

node_coords = []

# Draw nodes
for n, layer in enumerate(layer_info):
    layer_size = layer["nodes"]
    layer_top = v_spacing * (layer_size - 1) / 2. + (top + bottom) / 2.
    
    coords = []
    for m in range(layer_size):
        x = n * h_spacing + left
        y = layer_top - m * v_spacing
        
        # Color based on layer type
        if n == 0: color = '#a1c9f4' # Light blue for input
        elif n == n_layers - 1: color = '#ffb482' # Light orange for output
        else: color = '#8de5a1' # Light green for hidden
            
        circle = plt.Circle((x, y), v_spacing / 3.5, color=color, ec='#333333', zorder=4, lw=1.5)
        ax.add_artist(circle)
        coords.append((x, y))
        
        # Add details text if available
        if layer["details"] and m < len(layer["details"]):
            if n == 0:
                ax.text(x - 0.04, y, layer["details"][m], ha='right', va='center', fontsize=11, fontweight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
            elif n == n_layers - 1:
                ax.text(x + 0.04, y, layer["details"][m], ha='left', va='center', fontsize=12, fontweight='bold', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=1))
                
        # Add dots for hidden layers to represent many nodes
        if not layer["details"] and m == layer_size // 2:
            ax.text(x, y, '...', ha='center', va='center', fontsize=16, fontweight='bold', color='#333333', zorder=5)
            
    node_coords.append(coords)
    
    # Layer Titles
    ax.text(n * h_spacing + left, top + 0.08, layer["name"], ha='center', va='bottom', fontsize=13, fontweight='bold', color='#222222')
    ax.text(n * h_spacing + left, top + 0.06, layer["label"], ha='center', va='top', fontsize=11, color='#555555')

# Draw edges
for n in range(n_layers - 1):
    for pt1 in node_coords[n]:
        for pt2 in node_coords[n+1]:
            line = plt.Line2D([pt1[0], pt2[0]], [pt1[1], pt2[1]], c='#888888', alpha=0.8, zorder=1, lw=1.2)
            ax.add_artist(line)

plt.title("Arsitektur Multilayer Perceptron (MLP) - Prediksi Harga Sapphire Residence", fontsize=18, fontweight='bold', pad=40)

# Add Legend or Info Box
info_text = (
    "Detail Arsitektur:\n"
    "• Input: 6 Variabel Independen\n"
    "• Hidden Layers: 3 Lapis (64, 32, 16 neuron)\n"
    "• Fungsi Aktivasi Hidden: ReLU\n"
    "• Optimizer: L-BFGS / Adam / SGD\n"
    "• Output: 1 Variabel Dependen (Harga KPR)"
)
props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='#aaaaaa')
ax.text(0.5, -0.05, info_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', horizontalalignment='center', bbox=props, linespacing=1.5)

# Save image
output_filename = 'Arsitektur_MLP_Sapphire.png'
plt.savefig(output_filename, dpi=300, bbox_inches='tight', facecolor='white')
print(f"Diagram berhasil disimpan sebagai {output_filename}")
