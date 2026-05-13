import re

with open('z:\\SHIFQ\\app\\templates\\patients\\detail.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Update medication display in renderOrdonnances
old_display = """const meds = ordo.medications || [];
                return meds.length ? `<div class="text-sm space-y-1">${meds.map(m => `<div>• ${m.name}${m.dose ? ` (${m.dose})` : ''}</div>`).join('')}</div>` : '<span class="text-slate-500 text-sm">No medications</span>';"""

new_display = """const meds = ordo.medications || [];
                return meds.length ? `<div class="text-sm space-y-1">${meds.map(m => {
                  const dose = m.dose && m.dose !== 'As prescribed' ? m.dose : '';
                  const freq = m.frequency && m.frequency !== 'As prescribed' ? m.frequency : '';
                  const dur = m.duration && m.duration !== 'As prescribed' ? m.duration : '';
                  const method = m.method && m.method !== 'oral' ? ` (${m.method})` : '';
                  const parts = [m.name, dose, freq, dur].filter(Boolean);
                  return `<div>• ${parts.join(' — ')}${method}</div>`;
                }).join('')}</div>` : '<span class="text-slate-500 text-sm">No medications</span>';"""

if old_display in content:
    content = content.replace(old_display, new_display)
    print("Updated medication display")
else:
    print("Medication display pattern not found")

with open('z:\\SHIFQ\\app\\templates\\patients\\detail.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
