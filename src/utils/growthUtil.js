/**
 * 식물의 성장 수치와 에너지를 바탕으로 현재 성장 상태를 계산합니다.
 * @param {number} growthScore - 성장도 (0~100)
 * @param {number} positiveEnergy - 긍정 에너지
 * @param {number} negativeEnergy - 부정 에너지
 * @returns {Object} { stage: string, formName: string, isPositive: boolean }
 */
const calculateGrowthState = (growthScore, positiveEnergy, negativeEnergy) => {
  const isPositive = positiveEnergy >= negativeEnergy;

  const growthTable = [
    { max: 4, stage: 'SEED', pos: '씨앗 🌰', neg: '심연에서 속삭이는 씨앗 🌰' },
    { max: 19, stage: 'SPROUT', pos: '싱그러운 떡잎 🌱', neg: '기어 다니는 심연의 떡잎 🌱' },
    { max: 39, stage: 'LEAF', pos: '생명력 넘치는 본잎 🪴', neg: '저주받은 광기의 본잎 🪴' },
    { max: 69, stage: 'BUD', pos: '희망을 품은 봉오리 🌷', neg: '뒤틀린 황천의 봉오리 🌷' },
    { max: 100, stage: 'FLOWER', pos: '축복의 꽃 🌸', neg: '종말의 꽃 🌸' }
  ];

  let currentStage = growthTable[growthTable.length - 1]; 
  for (const tier of growthTable) {
    if (growthScore <= tier.max) {
      currentStage = tier;
      break;
    }
  }

  return {
    stage: currentStage.stage,
    formName: isPositive ? currentStage.pos : currentStage.neg,
    isPositive: isPositive
  };
};

module.exports = {
  calculateGrowthState
};
