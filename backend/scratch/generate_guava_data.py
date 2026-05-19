import os
import sys
import json
from groq import Groq

# Add workspace to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.config.settings import get_settings
from backend.utils.logger import logger

settings = get_settings()

GUIDE_PROMPT = """You are an expert precision agronomist specializing in Indian fruit horticulture.
Your task is to generate a comprehensive, highly detailed agricultural farming guide and biological stage profile for Guava (scientific name: Psidium guajava, often spelled as "Guava" or "Govva" in regional Indian contexts).

You must generate all the details, instructions, parameters, and scientific recommendations entirely by yourself based on your expert knowledge of Guava cultivation in India. Do NOT use placeholder text or generic answers.

Output your response as a single, valid JSON object with the following exact keys and structure:

{
  "guide": {
    "crop_name": "Guava",
    "scientific_name": "Psidium guajava",
    "category": "Fruits",
    "total_duration_days": 150,
    "water_requirement_mm": 1000,
    "temperature_optimal_c": "20-35",
    "preferred_soils": ["loam", "sandy loam", "clay loam"],
    "complete_farming_guide": {
      "step_1_soil_preparation": {
        "title": "Soil Preparation & Pit Digging",
        "timing": "1-2 months before planting",
        "steps": [
          "Select deep, well-drained loamy to sandy loam soil with pH 6.0 to 7.5. Dig pits of 60x60x60 cm or 1x1x1 m size during summer. Expose pits to sun for 15-20 days for solarization and sterilization. Fill each pit with a mixture of topsoil, 15-20 kg of well-decomposed Farmyard Manure (FYM), 1 kg Single Super Phosphate (SSP), and 100g Neem cake to prevent termite attacks."
        ]
      },
      "step_2_propagation_and_planting": {
        "title": "Propagation & High-Density Planting",
        "timing": "Onset of monsoon (June-August)",
        "steps": [
          "Use air-layered (gootee) or grafted plants from certified nurseries for early fruiting and uniform quality. Standard spacing: 5m x 5m or 6m x 6m (approx. 277-400 plants/ha). High-Density Planting (HDP): 3m x 2m (approx. 1666 plants/ha) or Meadow orchard system (2m x 1m). Carefully plant the sapling in the center of the pre-filled pit without damaging the root ball. Stake the young plants to protect them from strong winds and irrigate immediately after planting."
        ]
      },
      "step_3_training_and_pruning": {
        "title": "Training & Pruning (Bahar Treatment)",
        "timing": "Throughout vegetative phase / post-harvest",
        "steps": [
          "Train young plants to a single stem up to 60-70 cm to form a strong framework of 3-4 primary branches. Perform regular pruning to remove dry, diseased, water sprouts, and crisscrossing branches. For Bahar treatment (regulating flowering), withhold water for 3-4 weeks to induce dormancy, followed by light root exposure or root pruning. Prune 50% of the current season's shoots to 10-15 cm to stimulate fresh vegetative growth and heavy flowering."
        ]
      },
      "step_4_irrigation_management": {
        "title": "Irrigation Management & Recovery Strategy",
        "timing": "Throughout production cycle",
        "steps": [
          "Apply drip irrigation: most efficient system, saving 50-60% water while boosting yield. Irrigate young plants every 2-3 days in summer and 7-10 days in winter. Critical moisture stages: Flowering and Fruit Development stages. Water stress during fruit set causes heavy fruit drop. Avoid waterlogging as Guava is sensitive to root rot and collar rot under saturated conditions. Total water requirement: 1000 mm annually. Frequency is managed via crop evapotranspiration coefficients."
        ]
      },
      "step_5_fertilizer_application": {
        "title": "Fertilizer & Micronutrient Application",
        "schedule": [
          {
            "timing": "Basal / Pre-Pruning (at onset of monsoon)",
            "fertilizers": "Apply 20-30 kg of well-decomposed FYM, 300g Nitrogen (approx 650g Urea), 200g Phosphorus (approx 1.25 kg SSP), and 300g Potassium (approx 500g MOP) per fully mature tree (6 years and older) to ensure optimal canopy development and high yields."
          },
          {
            "timing": "Fruit Set Stage (October-November)",
            "fertilizers": "Apply a top dressing of 150g Nitrogen (325g Urea) and 150g Potassium (250g MOP) per tree to support rapid fruit bulking and size development."
          },
          {
            "timing": "Foliar Spray for Micronutrients",
            "fertilizers": "Apply a foliar spray of 0.5% Zinc Sulphate and 0.2% Boric Acid at pre-flowering and fruit set stages. This prevents zinc bronzing, reduces fruit cracking, and significantly improves fruit sweetness and Vitamin C content."
          }
        ]
      },
      "step_6_weed_management": {
        "title": "Weed Management & Intercropping",
        "steps": [
          "Keep the tree basins weed-free by regular shallow hoeing and hand weeding. Apply organic mulching (paddy straw, coconut husk, or dry leaves) to a thickness of 8-10 cm around the tree basin to conserve moisture and suppress weeds. Grow short-duration leguminous crops (cowpea, black gram, green gram) or vegetables as intercrops in the interspaces during the first 3-4 years to enrich soil and earn additional income."
        ]
      },
      "step_7_pest_management": {
        "title": "Pest Management",
        "pests": [
          {
            "pest": "Guava Fruit Fly",
            "symptoms": "Adult female oviposits under fruit skin; maggots feed on pulp causing fruit decay and premature drop.",
            "control": "Install methyl eugenol pheromone traps @ 10 traps/ha. Collect and destroy fallen infested fruits. Spray Dimethoate 30 EC @ 2 ml/litre."
          },
          {
            "pest": "Bark Eating Caterpillar",
            "symptoms": "Winding galleries made of frass and silk on tree bark; boring holes into branches.",
            "control": "Clean the affected bark, insert a wire to kill caterpillar, or inject 5 ml of Dichlorvos (0.05%) or petrol into the tunnel and plug with wet mud."
          },
          {
            "pest": "Tea Mosquito Bug",
            "symptoms": "Nymphs and adults suck sap from tender shoots and fruits; brown water-soaked spots on fruits, drying of shoots.",
            "control": "Spray Malathion 50 EC @ 2 ml/litre or Quinalphos 25 EC @ 2 ml/litre during early morning hours."
          }
        ]
      },
      "step_8_disease_management": {
        "title": "Disease Management",
        "diseases": [
          {
            "disease": "Guava Wilt",
            "symptoms": "Yellowing and wilting of leaves, rapid drying of twigs, root decay, discoloration of wood; fatal.",
            "control": "Maintain strict sanitation. Drench soil around infected trees with Carbendazim (0.2%) or apply Trichoderma viride @ 250g per tree mixed with FYM. Avoid waterlogging."
          },
          {
            "disease": "Anthracnose",
            "symptoms": "Sunken dark brown spots on leaves, branches, and fruits (mummified fruits). Dies back from tip.",
            "control": "Prune and burn infected twigs. Spray Copper Oxychloride (0.3%) or Carbendazim (0.1%) at 15-day intervals."
          },
          {
            "disease": "Fruit Canker",
            "symptoms": "Elevated, circular, corky brown lesions on fruit surface; reduces market value.",
            "control": "Spray Bordeaux mixture (1%) or Copper Oxychloride @ 3g/litre at monthly intervals during fruit development."
          }
        ]
      },
      "step_9_harvesting": {
        "title": "Harvesting",
        "timing": "Day 121-150 (production cycle)",
        "steps": [
          "Harvest fruits when they reach full maturity, indicated by a shift in skin color from dark green to light green or pale yellow. Harvest individually by hand-picking to avoid bruising. Expected yield is 20-25 tonnes per hectare for a well-maintained mature orchard."
        ]
      },
      "step_10_post_harvest": {
        "title": "Post-Harvest Handling & Packaging",
        "steps": [
          "Sort fruits to remove bruised, deformed, or diseased ones. Grade according to size, weight, and color. Pre-cool fruits to 8-10°C to increase shelf life. Pack in corrugated fiberboard boxes lined with newsprint or foam sheets. Store at 8-10°C and 85-90% Relative Humidity for 2-3 weeks."
        ]
      }
    }
  },
  "bio_profile": {
    "name": "Guava",
    "season": "zaid",
    "duration_days": 150,
    "water_req_mm": 1000.0,
    "osmotic_shock_sensitive": true,
    "rrc_max_mm_per_cycle": 20.0,
    "rrc_stage_split": [0.5, 0.5],
    "temp_stress_threshold_c": 38.0,
    "temp_optimal_min_c": 20.0,
    "temp_optimal_max_c": 35.0,
    "tsi_threshold": 45.0,
    "kc_json": {
      "initial": 0.5,
      "development": 0.65,
      "mid": 0.8,
      "late": 0.65,
      "harvest": 0.5
    },
    "stages_json": [
      {
        "name": "Pruning & Shooting",
        "start": 0,
        "end": 30,
        "min_m": 60,
        "max_m": 75
      },
      {
        "name": "Flowering & Fruit Set",
        "start": 31,
        "end": 60,
        "min_m": 65,
        "max_m": 80
      },
      {
        "name": "Fruit Development",
        "start": 61,
        "end": 120,
        "min_m": 70,
        "max_m": 85
      },
      {
        "name": "Maturity & Harvest",
        "start": 121,
        "end": 150,
        "min_m": 50,
        "max_m": 65
      }
    ],
    "soil_type": "loam"
  }
}

You must fill out all the descriptions, steps, control lists, and symptoms with robust, scientifically accurate, and comprehensive horticultural advice.
Do not include any prefix or suffix, markdown wraps, or explanation outside of the valid JSON structure.
"""

def main():
    logger.info("Connecting to Groq to dynamically generate Guava RAG and biological parameters...")
    client = Groq(api_key=settings.GROQ_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model=getattr(settings, "GROQ_CHAT_MODEL", "llama-3.3-70b-versatile"),
            messages=[
                {"role": "system", "content": "You are a professional agronomist and JSON generator. Generate the complete, comprehensive JSON block containing high-fidelity content generated entirely by yourself based on your agronomic knowledge. Do not use placeholders or generic lists. Return ONLY raw JSON."},
                {"role": "user", "content": GUIDE_PROMPT}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        raw_content = response.choices[0].message.content.strip()
        
        # Clean any accidental markdown fence wraps
        if raw_content.startswith("```"):
            lines = raw_content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()
            
        data = json.loads(raw_content)
        
        # Ensure directories exist
        os.makedirs("backend/data/guides", exist_ok=True)
        
        # 1. Save Guava RAG crop guide
        guide_path = "backend/data/guides/guava_cropguide.json"
        guide_season_format = {
            "season": "Zaid",
            "crops": [data["guide"]]
        }
        with open(guide_path, "w", encoding="utf-8") as f:
            json.dump(guide_season_format, f, indent=4, ensure_ascii=False)
            
        logger.info(f"Successfully generated and wrote RAG crop guide to: {guide_path}")
        
        # 2. Save Guava Crop biological config
        config_path = "backend/data/guava_crop_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data["bio_profile"], f, indent=4, ensure_ascii=False)
            
        logger.info(f"Successfully generated and wrote bio profile config to: {config_path}")
        
        print("Guava (Govva) RAG and Stage data generated successfully by your model!")
        print(f"RAG guide file: {guide_path}")
        print(f"Bio profile config file: {config_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate Guava data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
