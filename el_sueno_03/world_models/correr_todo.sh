#!/usr/bin/env bash
# Corre el experimento completo de Ha & Schmidhuber (2018), VizDoom Take Cover. CC0.
# Uso: S2_RNN_EPOCAS=400 nohup ./correr_todo.sh > corrida.log 2>&1 &
set -euo pipefail
cd "$(dirname "$0")"
echo "== inicio $(date)"; python -c "import torch;print('cuda:',torch.cuda.is_available())"
[ -f "datos/${S2_MODO:-completo}/vae.pt" ]       || { echo "== 1 recolectar $(date)"; python s1_recolectar.py ${NPROC:-24}; echo "== 2 VAE $(date)"; python s2_entrenar_vae.py; }
[ -f "datos/${S2_MODO:-completo}/series.npz" ]   || { echo "== 3 codificar $(date)"; python s3_codificar.py; }
# ahorro de disco: tras codificar, solo se conservan los primeros 400 rollouts (para visualizaciones)
if [ "${PODAR:-1}" = 1 ]; then ls datos/${S2_MODO:-completo}/rollouts/*.npz | sort | tail -n +401 | xargs -r rm -f; fi
df -h . | tail -1
[ -f "datos/${S2_MODO:-completo}/mdnrnn.pt" ]    || { echo "== 4 MDN-RNN $(date)"; python s4_entrenar_mdnrnn.py; }
for tau in ${TAUS:-1.15}; do
  echo "== 5 CMA-ES en el sueño τ=$tau $(date)"; S2_TAU=$tau python s5_cma_en_sueno.py
  echo "== 6 juego real τ=$tau $(date)"; python s6_evaluar_real.py $tau
done
echo "== fin $(date)"
