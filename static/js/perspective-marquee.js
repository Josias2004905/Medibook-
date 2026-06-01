/**
 * PerspectiveMarquee — 3D perspective scrolling text (MediBook specialties)
 */
(function (global) {
  'use strict';

  var DEFAULT_ITEMS = [
  'Cardiology', 'Dermatology', 'Pediatrics', 'Neurology', 'Orthopedics',
  'Ophthalmology', 'Dentistry', 'Gynecology', 'Radiology', 'General Medicine'
  ];

  function PerspectiveMarquee(container, items, options) {
    this.container = container;
    var fallbackUrl = container.getAttribute('data-fallback-url') || '#';
    this.items = (items && items.length) ? items : DEFAULT_ITEMS.map(function (n) {
      return { name: n, url: fallbackUrl };
    });
    this.opts = Object.assign({
      fontSize: 72,
      color: '#F0F4FF',
      fontWeight: 700,
      pixelsPerFrame: 2,
      rotateY: -28,
      rotateX: 8,
      perspective: 1200,
      fadeColor: '#060B14',
      background: 'transparent',
      speed: 1,
      height: 200
    }, options || {});

    this.offset = 0;
    this.approxWidth = 0;
    this.itemSpans = [];
    this.track = null;
    this.rafId = null;
    this.lastTime = 0;
    this.centerX = 0;

    this._build();
    this._measure();
    this._animate();
  }

  PerspectiveMarquee.prototype._build = function () {
    var o = this.opts;
    this.container.innerHTML = '';
    this.container.classList.add('perspective-marquee');
    this.container.style.position = 'relative';
    this.container.style.width = '100%';
    this.container.style.height = o.height + 'px';
    this.container.style.background = o.background;
    this.container.style.overflow = 'hidden';
    this.container.style.display = 'flex';
    this.container.style.alignItems = 'center';
    this.container.style.justifyContent = 'center';
    this.container.style.perspective = o.perspective + 'px';

    var tilt = document.createElement('div');
    tilt.className = 'perspective-marquee-tilt';
    tilt.style.cssText =
      'width:100%;display:flex;align-items:center;justify-content:flex-start;' +
      'transform:rotateX(' + o.rotateX + 'deg) rotateY(' + o.rotateY + 'deg);transform-style:preserve-3d;';

    this.track = document.createElement('div');
    this.track.className = 'perspective-marquee-track';
    this.track.style.cssText = 'display:flex;white-space:nowrap;will-change:transform;';

    var names = this.items.map(function (it) { return typeof it === 'string' ? it : it.name; });
    var tripled = names.concat(names).concat(names);
    var self = this;

    tripled.forEach(function (name, i) {
      var src = self.items[i % self.items.length];
      var url = typeof src === 'object' && src.url ? src.url : '#';
      var span = document.createElement('a');
      span.href = url;
      span.className = 'perspective-marquee-item';
      span.textContent = name;
      span.style.cssText =
        'display:inline-block;font-family:var(--font-heading),Syne,sans-serif;' +
        'font-size:' + o.fontSize + 'px;font-weight:' + o.fontWeight + ';color:' + o.color + ';' +
        'letter-spacing:-0.03em;text-decoration:none;transition:filter 0.1s,opacity 0.1s;';
      var pad = o.fontSize * 0.9;
      span.style.paddingRight = pad + 'px';
      self.track.appendChild(span);
      self.itemSpans.push(span);
    });

    tilt.appendChild(this.track);
    this.container.appendChild(tilt);

    var fadeH = document.createElement('div');
    fadeH.className = 'perspective-marquee-fade';
    fadeH.style.cssText =
      'position:absolute;inset:0;pointer-events:none;' +
      'background:linear-gradient(90deg,' + o.fadeColor + ' 0%,transparent 18%,transparent 82%,' + o.fadeColor + ' 100%);';

    var fadeV = document.createElement('div');
    fadeV.style.cssText =
      'position:absolute;inset:0;pointer-events:none;' +
      'background:linear-gradient(180deg,' + o.fadeColor + ' 0%,transparent 25%,transparent 75%,' + o.fadeColor + ' 100%);';

    this.container.appendChild(fadeH);
    this.container.appendChild(fadeV);
  };

  PerspectiveMarquee.prototype._measure = function () {
    var o = this.opts;
    var pad = o.fontSize * 0.9;
    var baseItems = this.items.map(function (it) { return typeof it === 'string' ? it : it.name; });
    this.approxWidth = baseItems.reduce(function (acc, item) {
      return acc + item.length * o.fontSize * 0.6 + pad;
    }, 0);
    this.centerX = this.container.clientWidth / 2;
  };

  PerspectiveMarquee.prototype._updateItems = function () {
    var o = this.opts;
    var center = this.centerX || 640;
    var itemCount = this.items.length;
    var sliceWidth = this.approxWidth / itemCount;

    for (var i = 0; i < this.itemSpans.length; i++) {
      var itemCenter = i * sliceWidth + sliceWidth / 2 + this.offset;
      var norm = (itemCenter - center) / center;
      var distance = Math.min(1, Math.abs(norm));
      var blurPx = distance * 6;
      var opacity = 1 - distance * 0.4;
      this.itemSpans[i].style.filter = 'blur(' + blurPx + 'px)';
      this.itemSpans[i].style.opacity = String(opacity);
    }
  };

  PerspectiveMarquee.prototype._tick = function (now) {
    if (!this.lastTime) this.lastTime = now;
    var dt = (now - this.lastTime) / 1000;
    this.lastTime = now;

    var pxPerSec = this.opts.pixelsPerFrame * 60 * this.opts.speed;
    this.offset -= pxPerSec * dt;
    if (this.approxWidth > 0) {
      while (this.offset <= -this.approxWidth) this.offset += this.approxWidth;
    }

    this.track.style.transform = 'translateX(' + this.offset + 'px)';
    this._updateItems();
    this.rafId = requestAnimationFrame(this._tick.bind(this));
  };

  PerspectiveMarquee.prototype._animate = function () {
    if (this.rafId) cancelAnimationFrame(this.rafId);
    this.lastTime = 0;
    this.rafId = requestAnimationFrame(this._tick.bind(this));
  };

  PerspectiveMarquee.prototype.destroy = function () {
    if (this.rafId) cancelAnimationFrame(this.rafId);
    this.container.innerHTML = '';
  };

  global.PerspectiveMarquee = PerspectiveMarquee;
})(window);
