const { calculateGrowthState } = require('../utils/growthUtil');

/**
 * [POST] /api/plants/:id/care
 * 식물 돌봄 행동 (물주기, 쓰다듬기 등)
 */
const carePlant = async (req, res) => {
  try {
    const { id: plantId } = req.params;
    const { actionType } = req.body; 

    const currentGrowthScore = 25;
    const currentPosEnergy = 10;
    const currentNegEnergy = 2;

    const growthDelta = 2; 
    const posEnergyDelta = 1;

    const newGrowthScore = currentGrowthScore + growthDelta;
    const newPosEnergy = currentPosEnergy + posEnergyDelta;
    
    const newState = calculateGrowthState(newGrowthScore, newPosEnergy, currentNegEnergy);

    return res.status(200).json({
      success: true,
      message: '돌봄 행동이 성공적으로 적용되었습니다.',
      data: {
        plantId: plantId,
        actionType: actionType,
        changes: {
          growthDelta: growthDelta,
          positiveDelta: posEnergyDelta,
          negativeDelta: 0
        },
        currentStatus: {
          growthScore: newGrowthScore,
          positiveEnergy: newPosEnergy,
          negativeEnergy: currentNegEnergy,
          stage: newState.stage,
          formName: newState.formName,
          isPositive: newState.isPositive
        }
      }
    });
  } catch (error) {
    return res.status(500).json({ success: false, message: '서버 에러 발생' });
  }
};

/**
 * [POST] /api/plants/:id/chat
 * AI 식물 대화 처리
 */
const chatPlant = async (req, res) => {
  try {
    const { id: plantId } = req.params;
    const { message } = req.body; 

    const posEnergyDelta = 1;
    const negEnergyDelta = 0;
    const growthDelta = 1;

    const newGrowthScore = 45; 
    const newPosEnergy = 20;
    const newNegEnergy = 5;

    const newState = calculateGrowthState(newGrowthScore, newPosEnergy, newNegEnergy);

    return res.status(200).json({
      success: true,
      message: '식물이 대답했습니다.',
      data: {
        plantId: plantId,
        reply: '네 칭찬을 들으니 잎이 더 넓어지는 기분이야! 정말 고마워.',
        sentiment: 'POSITIVE',
        changes: {
          growthDelta: growthDelta,
          positiveDelta: posEnergyDelta,
          negativeDelta: negEnergyDelta
        },
        currentStatus: {
          growthScore: newGrowthScore,
          positiveEnergy: newPosEnergy,
          negativeEnergy: newNegEnergy,
          stage: newState.stage,
          formName: newState.formName,
          isPositive: newState.isPositive
        }
      }
    });
  } catch (error) {
    return res.status(500).json({ success: false, message: '서버 에러 발생' });
  }
};

module.exports = {
  carePlant,
  chatPlant
};
