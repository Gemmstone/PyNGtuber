const animations = {
  None: function(shape, { speed, iteration, direction, center_x, center_y }) {

    const isInfinite = iteration === 'infinite';
    const tween = new Konva.Tween({
        node: shape,
        yoyo: true,
        repeat: isInfinite ? -1 : totalIterations - 1
    });

    return {
      play: function() {
        tween.play();
      },
      reset: function() {
        tween.reset();
      },
      finish: function() {
        tween.finish();
      }
    };
  },

  floaty: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const initialY = center_y;
    const distance = 20;
    let directionMultiplier = 1;

    if (direction === 'reverse') {
        directionMultiplier = -1;
    }

    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration * 2;

    const tween = new Konva.Tween({
        node: shape,
        y: initialY + (directionMultiplier * distance),
        duration: speed / 2,
        easing: easing,
        yoyo: true,
        repeat: isInfinite ? -1 : totalIterations - 1
    });

    return {
        play: function() {
            tween.play();
        },
        reset: function() {
            tween.reset();
            shape.y(initialY);
        },
        finish: function() {
            tween.finish();
            shape.y(initialY);
        }
    };
  },

  floatx: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const initialX = center_x;
    const distance = 20;
    let directionMultiplier = 1;

    if (direction === 'reverse') {
        directionMultiplier = -1;
    }

    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration;

    const tween = new Konva.Tween({
        node: shape,
        x: initialX + (directionMultiplier * distance),
        duration: speed / 2,
        easing: easing,
        yoyo: true,
        repeat: isInfinite ? -1 : totalIterations - 1
    });

    shape.x(initialX);

    return {
        play: function() {
            tween.play();
        },
        reset: function() {
            tween.reset();
            shape.x(initialX);
        },
        finish: function() {
            tween.finish();
            shape.x(initialX);
        }
    };
  },
  wing:  function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const distance = 0.7;
    let directionMultiplier = 1;

    if (direction === 'reverse') {
        directionMultiplier = -1;
    }

    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration;

    const tween = new Konva.Tween({
        node: shape,
        scaleX: directionMultiplier * distance,
        duration: speed / 2,
        easing: easing,
        yoyo: true,
        repeat: isInfinite ? -1 : totalIterations - 1
    });

    shape.scaleX(1);

    return {
        play: function() {
            tween.play();
        },
        reset: function() {
            tween.reset();
            shape.scaleX(1);
        },
        finish: function() {
            tween.finish();
            shape.scaleX(1);
        }
    };
  },

  shake: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const initialX = center_x;
    const distance = 20;
    let directionMultiplier = 1;

    if (direction === 'reverse') {
        directionMultiplier = -1;
    }

    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration;

    shape.x(initialX - (distance * directionMultiplier)/2);

    const tween = new Konva.Tween({
        node: shape,
        x: initialX + ((directionMultiplier * distance) / 2),
        duration: speed / 2,
        easing: easing,
        yoyo: true,
        repeat: isInfinite ? -1 : totalIterations - 1
    });

    shape.x(initialX);

    return {
        play: function() {
            tween.play();
        },
        reset: function() {
            tween.reset();
            shape.x(initialX);
        },
        finish: function() {
            tween.finish();
            shape.x(initialX);
        }
    };
  },

  gelatine: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const scaleValues = [
      { scaleX: 1, scaleY: 1 },
      { scaleX: 0.9, scaleY: 1.1 },
      { scaleX: 1.1, scaleY: 0.9 },
      { scaleX: 0.95, scaleY: 1.05 },
      { scaleX: 1, scaleY: 1 }
    ];

    let directionMultiplier = 1;
    let currentStep = 0;
    if (direction === 'reverse') {
      directionMultiplier = -1;
      let currentStep = scaleValues.length;
    }

    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration * (scaleValues.length - 1);
    let tween;

    const animateStep = () => {
      if (currentStep >= scaleValues.length) {
        currentStep = 0;
        if (direction === 'reverse') {
          let currentStep = scaleValues.length -1;
        }
      }

      const { scaleX, scaleY } = scaleValues[currentStep];
      const nextStep = currentStep + directionMultiplier;
      const { scaleX: nextScaleX, scaleY: nextScaleY } = scaleValues[nextStep] || scaleValues[0];

      tween = new Konva.Tween({
        node: shape,
        scaleX: nextScaleX,
        scaleY: nextScaleY,
        duration: speed / (scaleValues.length - 1),
        easing: easing,
        onFinish: function() {
          if (isInfinite || currentStep < totalIterations - 1) {
            currentStep += directionMultiplier;
            animateStep();
          } else {
            shape.scale({ x: 1, y: 1 });
          }
        }
      });

      tween.play();
    };

    return {
      play: function() {
        currentStep = 0;
        animateStep();
      },
      reset: function() {
        if (tween) tween.destroy();
        currentStep = 0;
        shape.scale({ x: 1, y: 1 });
      },
      finish: function() {
        if (tween) tween.destroy();
        shape.scale({ x: 1, y: 1 });
      }
    };
  },

  gelatine2: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const scaleValues = [
      { scaleX: 1, scaleY: 1 },
      { scaleX: 0.95, scaleY: 1.005 },
      { scaleX: 1.005, scaleY: 0.95 },
      { scaleX: 1, scaleY: 1 }
    ];

    let directionMultiplier = 1;
    let currentStep = 0;
    if (direction === 'reverse') {
      directionMultiplier = -1;
      let currentStep = scaleValues.length -1;
    }
    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration * (scaleValues.length - 1);
    let tween;

    const animateStep = () => {
      if (currentStep >= scaleValues.length) {
        currentStep = 0;
        if (direction === 'reverse') {
          let currentStep = scaleValues.length -1;
        }
      }

      const { scaleX, scaleY } = scaleValues[currentStep];
      const nextStep = currentStep + 1;
      const { scaleX: nextScaleX, scaleY: nextScaleY } = scaleValues[nextStep] || scaleValues[0];

      tween = new Konva.Tween({
        node: shape,
        scaleX: nextScaleX,
        scaleY: nextScaleY,
        duration: speed / (scaleValues.length - 1),
        easing: easing,
        onFinish: function() {
          if (isInfinite || currentStep < totalIterations - 1) {
            currentStep++;
            animateStep();
          } else {
            shape.scale({ x: 1, y: 1 });
          }
        }
      });

      tween.play();
    };

    return {
      play: function() {
        currentStep = 0;
        animateStep();
      },
      reset: function() {
        if (tween) tween.destroy();
        currentStep = 0;
        shape.scale({ x: 1, y: 1 });
      },
      finish: function() {
        if (tween) tween.destroy();
        shape.scale({ x: 1, y: 1 });
      }
    };
  },

  wobble: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const transformValues = [
      { translateX: 0, rotate: 0 },
      { translateX: -25, rotate: -5 },
      { translateX: 20, rotate: 3 },
      { translateX: -15, rotate: -3 },
      { translateX: 10, rotate: 2 },
      { translateX: -5, rotate: -1 },
      { translateX: 0, rotate: 0 }
    ];

    let currentStep = 0;
    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration * (transformValues.length - 1);
    let tween;

    const animateStep = () => {
      if (currentStep >= transformValues.length) {
        currentStep = 0;
      }

      const { translateX, rotate } = transformValues[currentStep];
      const nextStep = currentStep + 1;
      const { translateX: nextTranslateX, rotate: nextRotate } = transformValues[nextStep] || transformValues[0];

      tween = new Konva.Tween({
        node: shape,
        x: center_x + nextTranslateX,
        rotation: nextRotate,
        duration: speed / (transformValues.length - 1),
        easing: easing,
        onFinish: function() {
          if (isInfinite || currentStep < totalIterations - 1) {
            currentStep++;
            animateStep();
          } else {
            shape.position({ x: center_x, y: center_y });
            shape.rotation(0);
          }
        }
      });

      tween.play();
    };

    return {
      play: function() {
        currentStep = 0;
        animateStep();
      },
      reset: function() {
        if (tween) tween.destroy();
        currentStep = 0;
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
      },
      finish: function() {
        if (tween) tween.destroy();
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
      }
    };
  },

  swing: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const rotateValues = [
      0, 15, -10, 5, -5, 0
    ];

    let currentStep = 0;
    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration * (rotateValues.length - 1);
    let tween;

    const animateStep = () => {
      if (currentStep >= rotateValues.length) {
        currentStep = 0;
      }

      const rotation = rotateValues[currentStep];
      const nextStep = currentStep + 1;
      const nextRotation = rotateValues[nextStep] || rotateValues[0];

      tween = new Konva.Tween({
        node: shape,
        rotation: nextRotation,
        duration: speed / (rotateValues.length - 1),
        easing: easing,
        onFinish: function() {
          if (isInfinite || currentStep < totalIterations - 1) {
            currentStep++;
            animateStep();
          } else {
            shape.rotation(0);
          }
        }
      });

      tween.play();
    };

    return {
      play: function() {
        currentStep = 0;
        animateStep();
      },
      reset: function() {
        if (tween) tween.destroy();
        currentStep = 0;
        shape.rotation(0);
      },
      finish: function() {
        if (tween) tween.destroy();
        shape.rotation(0);
      }
    };
  },

  ears: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const transformValues = [
      { translateX: 0, rotate: 0 },
      { translateX: -25, rotate: -5 },
      { translateX: 10, rotate: 3 },
      { translateX: 0, rotate: 0 },
      { translateX: -10, rotate: -3 },
      { translateX: 25, rotate: 5 },
      { translateX: 0, rotate: 0 }
    ];

    let currentStep = 0;
    const isInfinite = iteration === 'infinite';
    const totalIterations = isInfinite ? Infinity : iteration * (transformValues.length - 1);
    let tween;

    const animateStep = () => {
      if (currentStep >= transformValues.length) {
        currentStep = 0;
      }

      const { translateX, rotate } = transformValues[currentStep];
      const nextStep = currentStep + 1;
      const { translateX: nextTranslateX, rotate: nextRotate } = transformValues[nextStep] || transformValues[0];

      tween = new Konva.Tween({
        node: shape,
        x: center_x + nextTranslateX,
        rotation: nextRotate,
        duration: speed / (transformValues.length - 1),
        easing: easing,
        onFinish: function() {
          if (isInfinite || currentStep < totalIterations - 1) {
            currentStep++;
            animateStep();
          } else {
            shape.position({ x: center_x, y: center_y });
            shape.rotation(0);
          }
        }
      });

      tween.play();
    };

    return {
      play: function() {
        currentStep = 0;
        animateStep();
      },
      reset: function() {
        if (tween) tween.destroy();
        currentStep = 0;
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
      },
      finish: function() {
        if (tween) tween.destroy();
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
      }
    };
  },

  bee: function(shape, { speed, iteration, direction, center_x, center_y, easing }) {
    const distance = 10; // Distance of movement
    const rotationAngle = 30; // Max rotation angle

    let isInfinite = iteration === 'infinite';
    let totalIterations = isInfinite ? Infinity : iteration;
    let tweenX, tweenY, tweenRotate;

    const randomize = () => Math.random() * distance * (Math.random() > 0.5 ? 1 : -1);
    const randomizeRotation = () => Math.random() * rotationAngle * (Math.random() > 0.5 ? 1 : -1);

    const animateStep = () => {
      tweenX = new Konva.Tween({
        node: shape,
        x: center_x + randomize(),
        duration: speed / 2,
        easing: easing,
        onFinish: function() {
          if (isInfinite || totalIterations > 0) {
            if (!isInfinite) totalIterations--;
            animateStep();
          }
        }
      });

      tweenY = new Konva.Tween({
        node: shape,
        y: center_y + randomize(),
        duration: speed / 2,
        easing: easing
      });

      tweenRotate = new Konva.Tween({
        node: shape,
        rotation: randomizeRotation(),
        duration: speed / 2,
        easing: easing
      });

      tweenX.play();
      tweenY.play();
      tweenRotate.play();
    };

    return {
      play: function() {
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
        animateStep();
      },
      reset: function() {
        if (tweenX) tweenX.destroy();
        if (tweenY) tweenY.destroy();
        if (tweenRotate) tweenRotate.destroy();
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
      },
      finish: function() {
        if (tweenX) tweenX.destroy();
        if (tweenY) tweenY.destroy();
        if (tweenRotate) tweenRotate.destroy();
        shape.position({ x: center_x, y: center_y });
        shape.rotation(0);
      }
    };
  },

};