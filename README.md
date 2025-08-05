# Penalty Shootout Game

A fun penalty shootout game built with Python and Pygame, featuring basic AI with different difficulty levels and smooth animations.

## Features

- **Interactive GUI**: Beautiful Pygame-based interface with smooth animations
- **Multiple Difficulty Levels**: Easy, Normal, and Hard modes with different AI behavior
- **Realistic Animations**: Ball follows parabolic trajectory with goalkeeper movements
- **Score Tracking**: Keep track of player vs computer scores
- **5-Round Matches**: Best of 5 penalty shootout format
- **Visual Feedback**: Clear goal/save animations and result messages

## Installation

1. **Install Python** (3.7 or higher recommended)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Or install pygame directly:
   ```bash
   pip install pygame
   ```

## How to Play

1. **Run the game**:
   ```bash
   python penalty_shootout.py
   ```

2. **Select Difficulty**:
   - **Easy**: Computer has 30% save chance, 40% guess accuracy
   - **Normal**: Computer has 50% save chance, 60% guess accuracy  
   - **Hard**: Computer has 70% save chance, 80% guess accuracy

3. **Gameplay**:
   - **Your Turn**: Click "Left", "Center", or "Right" to choose shot direction
   - **Computer's Turn**: Watch as the computer takes its penalty
   - **Saving**: When the computer shoots, you automatically try to save (40% success rate)
   - **5 Rounds**: First to score more goals wins!

## Game Mechanics

### Player Shooting
- Choose shot direction (Left, Center, Right)
- Ball animates with realistic parabolic trajectory
- Computer goalkeeper attempts to save based on difficulty

### Computer Shooting  
- Computer randomly chooses shot direction
- You automatically try to save (no manual input needed)
- 40% chance to successfully save any shot

### Difficulty Levels
- **Easy**: Computer is less accurate at guessing and saving
- **Normal**: Balanced gameplay
- **Hard**: Computer is very good at guessing and saving

## Controls

- **Mouse**: Click buttons to interact
- **Escape**: Close the game window
- **Menu Navigation**: Click buttons to select options

## Game States

1. **Main Menu**: Select difficulty and start game
2. **Playing**: Take turns shooting and saving penalties
3. **Game Over**: View final score and winner

## Technical Details

- **Language**: Python 3
- **Graphics**: Pygame
- **Animation**: Smooth ball movement with parabolic trajectories
- **AI**: Basic probability-based decision making
- **Resolution**: 800x600 pixels

## Future Enhancements

- Sound effects and background music
- More realistic goalkeeper animations
- Power meter for shot strength
- Tournament mode
- Statistics tracking
- Customizable game settings

Enjoy the game! ⚽ 