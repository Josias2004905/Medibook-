(function (global) {
  'use strict';

  var SPHERE_MATH = {
    deg2rad: function (d) { return d * (Math.PI / 180); },
    normalize: function (a) {
      while (a > 180) a -= 360;
      while (a < -180) a += 360;
      return a;
    }
  };

  /**
   * Inject global keyframe animations once.
   */
  (function () {
    if (typeof window.__doctorSphereStylesInjected !== 'undefined') return;
    window.__doctorSphereStylesInjected = true;
    var css =
      '@keyframes ds-fadeIn{from{opacity:0}to{opacity:1}}' +
      '@keyframes ds-scaleIn{from{transform:scale(0.8);opacity:0}to{transform:scale(1);opacity:1}}' +
      '.doctor-sphere-loader{background:rgba(255,255,255,0.03);border-radius:12px;display:flex;align-items:center;justify-content:center}' +
      '.doctor-sphere-loader-inner{text-align:center;color:rgba(240,244,255,0.4)}' +
      '.doctor-sphere-loader-inner .pulse{display:inline-block;width:48px;height:48px;border-radius:50%;border:3px solid rgba(10,255,233,0.15);border-top-color:var(--primary);animation:ds-spin 0.8s linear infinite}' +
      '@keyframes ds-spin{to{transform:rotate(360deg)}}';
    var style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
  })();

  function DoctorSphere(container, images, options) {
    this.container = container;
    this.images = images || [];
    this.opts = Object.assign({
      containerSize: 400,
      sphereRadius: 200,
      dragSensitivity: 0.5,
      momentumDecay: 0.95,
      maxRotationSpeed: 5,
      baseImageScale: 0.24,
      hoverScale: 1.2,
      perspective: 1000,
      autoRotate: false,
      autoRotateSpeed: 0.3
    }, options || {});

    this.rotation = { x: 15, y: 15, z: 0 };
    this.velocity = { x: 0, y: 0 };
    this.isDragging = false;
    this.hoveredIndex = null;
    this.selectedIndex = null;
    this.imagePositions = [];
    this.nodeEls = [];
    this.lastPointer = { x: 0, y: 0 };
    this.rafId = null;
    this.onSelect = null;
    this._isDestroyed = false;
    this._modalEl = null;

    this._build();
    if (this.images.length) {
      this._bind();
      this._animate();
    }
  }

  /* ── Loading / empty states ── */

  DoctorSphere.prototype._showLoader = function () {
    var o = this.opts;
    this.container.innerHTML =
      '<div class="doctor-sphere-loader" style="width:' + o.containerSize + 'px;height:' + o.containerSize + 'px;max-width:100%;">' +
        '<div class="doctor-sphere-loader-inner"><div class="pulse"></div><p style="margin-top:12px;font-size:0.85rem;">Loading doctors\u2026</p></div>' +
      '</div>';
  };

  DoctorSphere.prototype._showEmpty = function () {
    var o = this.opts;
    this.container.innerHTML =
      '<div class="doctor-sphere-empty" style="width:' + o.containerSize + 'px;height:' + o.containerSize + 'px;max-width:100%;display:flex;align-items:center;justify-content:center;">' +
        '<div style="text-align:center;color:rgba(240,244,255,0.35);">' +
          '<i class="fa-solid fa-user-doctor" style="font-size:2.5rem;opacity:0.25;margin-bottom:12px;"></i>' +
          '<p style="font-size:0.9rem;">No doctors available</p>' +
        '</div>' +
      '</div>';
  };

  /* ── DOM construction ── */

  DoctorSphere.prototype._build = function () {
    if (!this.images.length) {
      this._showEmpty();
      return;
    }

    var o = this.opts;
    var size = o.containerSize;

    this.container.innerHTML = '';
    this.container.style.width = size + 'px';
    this.container.style.height = size + 'px';
    this.container.style.maxWidth = '100%';
    this.container.style.margin = '0 auto';
    this.container.style.position = 'relative';
    this.container.style.perspective = o.perspective + 'px';
    this.container.className = 'doctor-sphere-root';

    this.stage = document.createElement('div');
    this.stage.className = 'doctor-sphere-stage';
    this.stage.style.width = size + 'px';
    this.stage.style.height = size + 'px';
    this.stage.style.position = 'relative';
    this.container.appendChild(this.stage);

    this.imagePositions = this._fibonacciPositions();
    this.nodeEls = [];

    for (var i = 0; i < this.images.length; i++) {
      var node = document.createElement('div');
      node.className = 'doctor-sphere-node';
      node.dataset.index = String(i);
      node.innerHTML = this._nodeHtml(this.images[i]);

      node.addEventListener('mouseenter', this._makeHoverHandler(i));
      node.addEventListener('mouseleave', this._makeUnhoverHandler());
      node.addEventListener('click', this._makeClickHandler(i));

      this.stage.appendChild(node);
      this.nodeEls.push(node);
    }

    this._render();
  };

  DoctorSphere.prototype._nodeHtml = function (doc) {
    var inner;
    if (doc.src) {
      inner = '<img src="' + doc.src + '" alt="' + this._esc(doc.name) + '" draggable="false" loading="lazy">';
    } else {
      inner = '<span class="doctor-sphere-initials">' + this._esc(doc.initials || '?') + '</span>';
    }
    return (
      '<div class="doctor-sphere-avatar">' + inner + '</div>' +
      '<div class="doctor-sphere-node-label">' + this._esc(doc.specialty || '') + '</div>'
    );
  };

  DoctorSphere.prototype._esc = function (s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  };

  /* ── Event handler factories (avoids per-frame closure allocation) ── */

  DoctorSphere.prototype._makeHoverHandler = function (idx) {
    var self = this;
    return function () { self.hoveredIndex = idx; self._render(); };
  };

  DoctorSphere.prototype._makeUnhoverHandler = function () {
    var self = this;
    return function () { self.hoveredIndex = null; self._render(); };
  };

  DoctorSphere.prototype._makeClickHandler = function (idx) {
    var self = this;
    return function (e) {
      if (self.isDragging) return;
      e.stopPropagation();
      self.selectedIndex = idx;
      self._render();
      self._showSpotlight(idx);
      if (typeof self.onSelect === 'function') {
        self.onSelect(self.images[idx], idx);
      }
    };
  };

  /* ── Fibonacci sphere positions ── */

  DoctorSphere.prototype._fibonacciPositions = function () {
    var positions = [];
    var n = this.images.length;
    if (!n) return positions;
    var radius = this.opts.sphereRadius;
    var goldenRatio = (1 + Math.sqrt(5)) / 2;
    var angleIncrement = 2 * Math.PI / goldenRatio;

    for (var i = 0; i < n; i++) {
      var t = i / n;
      var inclination = Math.acos(1 - 2 * t);
      var azimuth = angleIncrement * i;

      var phi = inclination * (180 / Math.PI);
      var theta = (azimuth * (180 / Math.PI)) % 360;

      var poleBonus = Math.pow(Math.abs(phi - 90) / 90, 0.6) * 35;
      if (phi < 90) phi = Math.max(5, phi - poleBonus);
      else phi = Math.min(175, phi + poleBonus);

      phi = 15 + (phi / 180) * 150;

      var randomOffset = (Math.random() - 0.5) * 20;
      theta = (theta + randomOffset) % 360;
      phi = Math.max(0, Math.min(180, phi + (Math.random() - 0.5) * 10));

      positions.push({ theta: theta, phi: phi, radius: radius });
    }
    return positions;
  };

  /* ── World position calculation with 3D rotation ── */

  DoctorSphere.prototype._worldPositions = function () {
    var o = this.opts;
    var radius = o.sphereRadius;
    var baseSize = o.containerSize * o.baseImageScale;
    var rotXRad = SPHERE_MATH.deg2rad(this.rotation.x);
    var rotYRad = SPHERE_MATH.deg2rad(this.rotation.y);
    var fadeZoneStart = -9999;
    var fadeZoneEnd = -99999;

    var positions = this.imagePositions.map(function (pos) {
      var thetaRad = SPHERE_MATH.deg2rad(pos.theta);
      var phiRad = SPHERE_MATH.deg2rad(pos.phi);

      var x = pos.radius * Math.sin(phiRad) * Math.cos(thetaRad);
      var y = pos.radius * Math.cos(phiRad);
      var z = pos.radius * Math.sin(phiRad) * Math.sin(thetaRad);

      // Y-axis rotation
      var x1 = x * Math.cos(rotYRad) + z * Math.sin(rotYRad);
      var z1 = -x * Math.sin(rotYRad) + z * Math.cos(rotYRad);
      x = x1; z = z1;

      // X-axis rotation
      var y2 = y * Math.cos(rotXRad) - z * Math.sin(rotXRad);
      var z2 = y * Math.sin(rotXRad) + z * Math.cos(rotXRad);
      y = y2; z = z2;

      var isVisible = z > fadeZoneEnd;
      var fadeOpacity = 1;
      if (z <= fadeZoneStart) {
        fadeOpacity = Math.max(0, (z - fadeZoneEnd) / (fadeZoneStart - fadeZoneEnd));
      }

      var isPole = pos.phi < 30 || pos.phi > 150;
      var dist2d = Math.sqrt(x * x + y * y);
      var maxDist = radius;
      var distRatio = Math.min(dist2d / maxDist, 1);
      var distPenalty = isPole ? 0.4 : 0.7;
      var centerScale = Math.max(0.3, 1 - distRatio * distPenalty);
      var depthScale = (z + radius) / (2 * radius);
      var scale = centerScale * Math.max(0.5, 0.8 + depthScale * 0.3);

      return {
        x: x, y: y, z: z,
        scale: scale,
        zIndex: Math.round(1000 + z),
        isVisible: isVisible,
        fadeOpacity: fadeOpacity,
        baseSize: baseSize
      };
    });

    // Collision detection
    for (var i = 0; i < positions.length; i++) {
      var p = positions[i];
      if (!p.isVisible) continue;
      var adjusted = p.scale;
      var sz = p.baseSize * adjusted;

      for (var j = 0; j < positions.length; j++) {
        if (i === j) continue;
        var oth = positions[j];
        if (!oth.isVisible) continue;
        var osz = oth.baseSize * oth.scale;
        var dx = p.x - oth.x;
        var dy = p.y - oth.y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        var minDist = (sz + osz) / 2 + 25;
        if (dist < minDist && dist > 0) {
          var overlap = minDist - dist;
          adjusted = Math.min(adjusted, adjusted * Math.max(0.4, 1 - (overlap / minDist) * 0.6));
        }
      }

      positions[i].scale = Math.max(0.25, adjusted);
    }

    return positions;
  };

  /* ── Render ── */

  DoctorSphere.prototype._render = function () {
    if (!this.nodeEls.length) return;
    var o = this.opts;
    var half = o.containerSize / 2;
    var world = this._worldPositions();

    for (var i = 0; i < this.nodeEls.length; i++) {
      var el = this.nodeEls[i];
      var p = world[i];
      if (!p || !p.isVisible) {
        el.style.display = 'none';
        continue;
      }
      el.style.display = 'block';
      var size = p.baseSize * p.scale;
      var isHovered = this.hoveredIndex === i;
      var isSelected = this.selectedIndex === i;
      var finalScale = isHovered ? Math.min(1.2, 1.2 / p.scale) : 1;

      el.style.width = size + 'px';
      el.style.height = size + 'px';
      el.style.left = (half + p.x) + 'px';
      el.style.top = (half + p.y) + 'px';
      el.style.opacity = String(p.fadeOpacity);
      el.style.zIndex = String(p.zIndex);
      el.style.transform = 'translate(-50%, -50%) scale(' + finalScale + ')';
      el.classList.toggle('is-hovered', isHovered);
      el.classList.toggle('is-selected', isSelected);
    }
  };

  /* ── Spotlight modal ── */

  DoctorSphere.prototype._showSpotlight = function (idx) {
    if (!this.images.length) return;
    var doc = this.images[idx];
    if (!doc) return;

    var existing = document.querySelector('.ds-spotlight-overlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.className = 'ds-spotlight-overlay';
    overlay.style.cssText =
      'position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;' +
      'padding:16px;background:rgba(0,0,0,0.3);animation:ds-fadeIn 0.3s ease-out;';

    var card = document.createElement('div');
    card.className = 'ds-spotlight-card';
    card.style.cssText =
      'background:#fff;border-radius:12px;max-width:400px;width:100%;overflow:hidden;' +
      'animation:ds-scaleIn 0.3s ease-out;';

    var imgWrap = document.createElement('div');
    imgWrap.style.cssText = 'position:relative;aspect-ratio:1;';
    var img = document.createElement('img');
    img.src = doc.src || '';
    img.alt = this._esc(doc.name);
    img.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;';
    if (!doc.src) {
      img.style.display = 'none';
      var initialBg = document.createElement('div');
      initialBg.style.cssText =
        'width:100%;height:100%;display:flex;align-items:center;justify-content:center;' +
        'background:linear-gradient(145deg,#f0f4ff,#e0e8f0);font-size:3rem;font-weight:800;' +
        'color:var(--primary,#0ae9a8);font-family:var(--font-heading,inherit);';
      initialBg.textContent = doc.initials || 'DR';
      imgWrap.appendChild(initialBg);
    }
    imgWrap.appendChild(img);

    var closeBtn = document.createElement('button');
    closeBtn.innerHTML = '&times;';
    closeBtn.style.cssText =
      'position:absolute;top:8px;right:8px;width:32px;height:32px;border-radius:50%;' +
      'border:none;background:rgba(0,0,0,0.5);color:#fff;font-size:18px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;transition:background 0.2s;';
    closeBtn.addEventListener('mouseenter', function () { closeBtn.style.background = 'rgba(0,0,0,0.7)'; });
    closeBtn.addEventListener('mouseleave', function () { closeBtn.style.background = 'rgba(0,0,0,0.5)'; });
    imgWrap.appendChild(closeBtn);

    card.appendChild(imgWrap);

    var body = document.createElement('div');
    body.style.cssText = 'padding:20px;';

    var nameEl = document.createElement('h3');
    nameEl.textContent = doc.name;
    nameEl.style.cssText = 'font-size:1.15rem;font-weight:700;margin:0 0 4px;color:#1a1a2e;';

    var specialtyEl = document.createElement('div');
    specialtyEl.textContent = doc.specialty || '';
    specialtyEl.style.cssText = 'font-size:0.85rem;font-weight:500;color:var(--primary,#0ae9a8);margin-bottom:4px;';

    var ratingEl = document.createElement('div');
    var full = Math.round(doc.rating || 0);
    ratingEl.innerHTML = '&#9733;&#9733;&#9733;&#9733;&#9733;'.slice(0, full) + '<span style="color:var(--text-muted, #999);font-size:0.8rem;margin-left:4px;">' + (doc.rating || '') + '</span>';
    ratingEl.style.cssText = 'margin-bottom:12px;';

    var bioEl = document.createElement('p');
    bioEl.textContent = doc.bio || '';
    bioEl.style.cssText = 'font-size:0.875rem;color:#555;line-height:1.7;margin:0 0 16px;';

    body.appendChild(nameEl);
    body.appendChild(specialtyEl);
    body.appendChild(ratingEl);
    body.appendChild(bioEl);

    if (doc.fee !== undefined && doc.url) {
      var footer = document.createElement('div');
      footer.style.cssText =
        'display:flex;justify-content:space-between;align-items:center;padding-top:16px;' +
        'border-top:1px solid #eee;';

      var feeEl = document.createElement('span');
      feeEl.textContent = '$' + doc.fee;
      feeEl.style.cssText = 'font-size:1.2rem;font-weight:700;color:var(--primary,#0ae9a8);';

      var bookBtn = document.createElement('a');
      bookBtn.href = doc.url;
      bookBtn.textContent = 'Book Now';
      bookBtn.style.cssText =
        'padding:10px 24px;border-radius:10px;border:none;background:var(--primary,#0ae9a8);' +
        'color:#060b14;font-weight:600;font-size:0.9rem;cursor:pointer;text-decoration:none;' +
        'transition:all 0.2s;';
      bookBtn.addEventListener('mouseenter', function () { bookBtn.style.opacity = '0.85'; });
      bookBtn.addEventListener('mouseleave', function () { bookBtn.style.opacity = '1'; });

      footer.appendChild(feeEl);
      footer.appendChild(bookBtn);
      body.appendChild(footer);
    }

    card.appendChild(body);

    overlay.appendChild(card);
    document.body.appendChild(overlay);
    this._modalEl = overlay;

    var self = this;
    function closeModal(e) {
      if (e.target === overlay || e.target === closeBtn) {
        overlay.remove();
        self._modalEl = null;
      }
    }
    overlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', function (e) { e.stopPropagation(); overlay.remove(); self._modalEl = null; });

    document.addEventListener('keydown', self._modalKeyHandler = function (e) {
      if (e.key === 'Escape' && self._modalEl) {
        self._modalEl.remove();
        self._modalEl = null;
        document.removeEventListener('keydown', self._modalKeyHandler);
      }
    });
  };

  /* ── Animation loop ── */

  DoctorSphere.prototype._tick = function () {
    if (!this.isDragging) {
      this.velocity.x *= this.opts.momentumDecay;
      this.velocity.y *= this.opts.momentumDecay;
      if (Math.abs(this.velocity.x) < 0.01) this.velocity.x = 0;
      if (Math.abs(this.velocity.y) < 0.01) this.velocity.y = 0;

      if (this.opts.autoRotate) {
        this.rotation.y = SPHERE_MATH.normalize(this.rotation.y + this.opts.autoRotateSpeed);
      }
      if (this.velocity.x || this.velocity.y) {
        this.rotation.x = SPHERE_MATH.normalize(this.rotation.x + this._clamp(this.velocity.x));
        this.rotation.y = SPHERE_MATH.normalize(this.rotation.y + this._clamp(this.velocity.y));
      }
    }
    this._render();
    this.rafId = requestAnimationFrame(this._tick.bind(this));
  };

  DoctorSphere.prototype._animate = function () {
    if (this.rafId) cancelAnimationFrame(this.rafId);
    this.rafId = requestAnimationFrame(this._tick.bind(this));
  };

  DoctorSphere.prototype._clamp = function (v) {
    return Math.max(-this.opts.maxRotationSpeed, Math.min(this.opts.maxRotationSpeed, v));
  };

  /* ── Drag / touch events ── */

  DoctorSphere.prototype._bind = function () {
    var self = this;

    this.container.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      e.preventDefault();
      self.isDragging = true;
      self.velocity = { x: 0, y: 0 };
      self.lastPointer = { x: e.clientX, y: e.clientY };
      self.container.classList.add('is-dragging');
    });

    document.addEventListener('mousemove', function (e) {
      if (!self.isDragging) return;
      var dx = e.clientX - self.lastPointer.x;
      var dy = e.clientY - self.lastPointer.y;
      var rx = -dy * self.opts.dragSensitivity;
      var ry = dx * self.opts.dragSensitivity;
      self.rotation.x = SPHERE_MATH.normalize(self.rotation.x + self._clamp(rx));
      self.rotation.y = SPHERE_MATH.normalize(self.rotation.y + self._clamp(ry));
      self.velocity = { x: self._clamp(rx), y: self._clamp(ry) };
      self.lastPointer = { x: e.clientX, y: e.clientY };
    });

    document.addEventListener('mouseup', function () {
      if (!self.isDragging) return;
      self.isDragging = false;
      self.container.classList.remove('is-dragging');
    });

    this.container.addEventListener('touchstart', function (e) {
      var t = e.touches[0];
      self.isDragging = true;
      self.velocity = { x: 0, y: 0 };
      self.lastPointer = { x: t.clientX, y: t.clientY };
      self.container.classList.add('is-dragging');
    }, { passive: true });

    document.addEventListener('touchmove', function (e) {
      if (!self.isDragging) return;
      e.preventDefault();
      var t = e.touches[0];
      var dx = t.clientX - self.lastPointer.x;
      var dy = t.clientY - self.lastPointer.y;
      var rx = -dy * self.opts.dragSensitivity;
      var ry = dx * self.opts.dragSensitivity;
      self.rotation.x = SPHERE_MATH.normalize(self.rotation.x + self._clamp(rx));
      self.rotation.y = SPHERE_MATH.normalize(self.rotation.y + self._clamp(ry));
      self.velocity = { x: self._clamp(rx), y: self._clamp(ry) };
      self.lastPointer = { x: t.clientX, y: t.clientY };
    }, { passive: false });

    document.addEventListener('touchend', function () {
      self.isDragging = false;
      self.container.classList.remove('is-dragging');
    });
  };

  /* ── Cleanup ── */

  DoctorSphere.prototype.destroy = function () {
    this._isDestroyed = true;
    if (this.rafId) cancelAnimationFrame(this.rafId);
    if (this._modalEl) { this._modalEl.remove(); this._modalEl = null; }
    if (this._modalKeyHandler) document.removeEventListener('keydown', this._modalKeyHandler);
    this.container.innerHTML = '';
  };

  global.DoctorSphere = DoctorSphere;
})(window);
