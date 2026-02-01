let matches = [];
let visibleMatches = 5;
let selectedMatch = null;


// ← AÑADIR ESTO AL FINAL DEL ARCHIVO
const teamLogos = {
  // Atlantic Division
  "Boston Celtics": "boston-celtics.svg",
  "Brooklyn Nets": "brooklyn-nets.svg", 
  "New York Knicks": "new-york-knicks.svg",
  "Philadelphia 76ers": "philidephia.svg",
  "Toronto Raptors": "toronto-raptors.svg",
  
  // Central Division
  "Chicago Bulls": "chicago-bulls.svg",
  "Cleveland Cavaliers": "cleveland-cavaliers.svg",
  "Detroit Pistons": "detroit-pistons.svg",
  "Indiana Pacers": "indiana-pacers.svg",
  "Milwaukee Bucks": "milwaukee-bucks-1.svg",
  
  // Southeast Division
  "Atlanta Hawks": "atlanta-hawks-basketball-club.svg",
  "Charlotte Hornets": "charlotte-hornets-2.svg",
  "Miami Heat": "miami-heat.svg",
  "Orlando Magic": "orlando-magic-1.svg",
  "Washington Wizards": "washington-wizards-3.svg",
  
  // Northwest Division
  "Denver Nuggets": "denver-nuggets-3.svg",
  "Minnesota Timberwolves": "minnesota-timberwolves-logo.svg",
  "Oklahoma City Thunder": "oklahoma-city-thunder-logo.svg",
  "Portland Trail Blazers": "portland-trail-blazers-logo.svg",
  "Utah Jazz": "utah-jazz-logo.svg",
  
  // Pacific Division
  "Golden State Warriors": "golden-state-warriors.svg",
  "LA Clippers": "los-angeles-clippers.svg",
  "Los Angeles Lakers": "los-angeles-lakers.svg",
  "Phoenix Suns": "phoenix-suns.svg",
  "Sacramento Kings": "sacramento-kings.svg",
  
  // Southwest Division
  "Dallas Mavericks": "dallas-mavericks-logo.svg",
  "Houston Rockets": "houston-rockets-logo.svg",
  "Memphis Grizzlies": "memphis-grizzlies-logo.svg",
  "New Orleans Pelicans": "new-orleans-pelicans-logo.svg",
  "San Antonio Spurs": "san-antonio-spurs-logo.svg"

}

// Función helper para obtener logo
function getTeamLogo(teamName) {
  return teamLogos[teamName] || "generic.svg";
}

fetch("/matches/upcoming?limit=10")
  .then(res => {
    console.log("STATUS:", res.status, res.statusText);  // ← CRÍTICO
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    return res.json();
  })
  .then(data => {
    console.log("DATA RECIBIDA:", data);  // ← CRÍTICO
    matches = Array.isArray(data) ? data : [];
    renderMatches();
  })
  .catch(error => {
    console.error("FETCH ERROR:", error);
    matches = [];
    renderMatches();  // ← Para que muestre "No hay partidos"
  });



function renderMatches() {
  const container = document.getElementById("matches");
  container.innerHTML = "";

  if (matches.length === 0) {
    container.innerHTML = "<p style='text-align:center;opacity:0.7;'>No hay partidos próximos</p>";
    return;
  }

  matches.slice(0, visibleMatches).forEach(match => {
    const div = document.createElement("div");
    div.className = "match";

    const homeLogo = teamLogos[match.home];
    const awayLogo = teamLogos[match.away];

    div.innerHTML = `
      <div class="match-visual">
        <img src="/static/${homeLogo}" class="team-logo" alt="${match.home}" onerror="this.src='/static/generic.svg'" />
        <img src="/static/basketball.svg" class="basketball predict-ball" data-match-id="${match.id}" alt="Predict" />
        <img src="/static/${awayLogo}" class="team-logo" alt="${match.away}" onerror="this.src='/static/generic.svg'" />
      </div>
      <div class="match-info">
        <strong>${match.home} vs ${match.away}</strong>
        <span>${new Date(match.date).toLocaleDateString('es-ES', {
          weekday: 'short', day: 'numeric', month: 'short'
        })}</span>
      </div>
    `;
    

     // ← CLICK EN BALÓN (MÉTODO DELEGADO - MÁS ROBUSTO)
    const basketball = div.querySelector(".predict-ball");
    basketball.addEventListener("click", function(e) {
      e.preventDefault();
      e.stopPropagation();
      const matchId = this.dataset.matchId;
      console.log("Click balón:", matchId); // ← DEBUG
      openModal(matchId);
    });

    container.appendChild(div);
  });

  // ← DELEGADO GLOBAL para todos los balones (por si acaso)
  /*container.addEventListener("click", function(e) {
    if (e.target.classList.contains("predict-ball")) {
      const matchId = e.target.dataset.matchId;
      openModal(matchId);
    }
  }); */

    
}



document.getElementById("matches").addEventListener("click", function (e) {
  const target = e.target;
  if (target && target.classList.contains("predict-ball")) {
    e.preventDefault();
    e.stopPropagation();
    const matchId = target.dataset.matchId;
    openModal(matchId);
  }
});



document.getElementById("loadMore").onclick = () => {
    visibleMatches = Math.min(visibleMatches + 5, matches.length);
    renderMatches();
};

function openModal(matchId) {
    selectedMatch = matches.find(m => m.id === matchId);
    
    const box = document.getElementById("predictionResult");

    
    if (box) {
      box.innerHTML = `
      <div style="text-align:center;opacity:0.6;">
      Selecciona un modelo para predecir
      </div>
      `;
    }


    document.getElementById("modal").classList.remove("hidden");
}


document.getElementById("closeModal").onclick = () => {
  // Limpia también al cerrar para que al volver a abrir esté vacío
  document.getElementById("predictionResult").innerHTML = "";
  selectedMatch = null;
  document.getElementById("modal").classList.add("hidden");
};

/*
document.getElementById("closeModal").onclick = () => {
    document.getElementById("modal").classList.add("hidden");
};

*/
document.getElementById("lstmBtn").onclick = () => predict("lstm");
document.getElementById("xgbBtn").onclick = () => predict("xgboost");




async function predict(model) {
  if (!selectedMatch) return;
  
  const endpoint = model === 'lstm' ? '/prediction/predict_lstm' : '/prediction/predict_xgb';
  
  try {

    // Limpia resultado anterior
    document.getElementById("predictionResult").innerHTML = '<div style="text-align:center;opacity:0.7;">Cargando predicción...</div>';
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        home_team: selectedMatch.home,
        away_team: selectedMatch.away,
        date: selectedMatch.date
      })
    });
    
    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log("DEBUG data:", data);  // ← AÑADE para verificar
    
    // ← FIXED: accede directo data.home_win_prob
    const homeProb = Math.round((data.home_win_prob || 0) * 100);
    const awayProb = Math.round((data.away_win_prob || 0) * 100);
    
    document.getElementById("predictionResult").innerHTML = `
      <div style="background: linear-gradient(45deg, #667eea, #764ba2); color:white; padding:25px; border-radius:20px; margin:20px 0; text-align:center;">
        <h4><strong>${model.toUpperCase()}</strong> Prediction</h4>
        <p><strong>${selectedMatch.home}: ${homeProb}%</strong></p>
        <p><strong>${selectedMatch.away}: ${awayProb}%</strong></p>
        <small>${new Date(selectedMatch.date).toLocaleDateString('es-ES')}</small>
      </div>
    `;
  } catch (error) {
    console.error("Error en predicción:", error);
    document.getElementById("predictionResult").innerHTML = `
      <div style="background: #fee; color: #c33; padding:20px; border-radius:10px; margin:20px 0;">
        ❌ Error: ${error.message}
      </div>
    `;
  }

}






