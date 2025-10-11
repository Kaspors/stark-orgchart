(async function () {
  const container = document.getElementById('chart');

  const res = await fetch('/api/tree');
  if (!res.ok) {
    container.innerHTML = `<div style="height:100%;display:flex;align-items:center;justify-content:center;color:#e6edf3">
      Failed to load (HTTP ${res.status})
    </div>`;
    return;
  }
  const nodesRaw = await res.json();
  if (!Array.isArray(nodesRaw) || nodesRaw.length === 0) {
    container.innerHTML = `<div style="height:100%;display:flex;align-items:center;justify-content:center;color:#e6edf3">
      <div style="text-align:center">
        <div style="font-weight:800;font-size:18px;margin-bottom:8px">No data yet</div>
        <a href="/admin" style="display:inline-block;background:#F5821E;color:#000;padding:10px 14px;border-radius:10px;font-weight:800;text-decoration:none">Open Admin</a>
      </div>
    </div>`;
    return;
  }

  const ids = new Set(nodesRaw.map(n => n.id));
  const tops = nodesRaw.filter(n => !n.parentId || !ids.has(n.parentId));
  const nodes = nodesRaw.map(n => ({...n}));
  if (tops.length !== 1) {
    const VROOT = '__virtual_root__';
    nodes.unshift({ id: VROOT, parentId: null, type: 'unit', name: 'STARK IT Delivery', unit_level: 'department' });
    for (const n of nodes) {
      if (n.id !== VROOT && (!n.parentId || !ids.has(n.parentId))) n.parentId = VROOT;
    }
  }

  const svg = d3.select(container).append('svg').attr('width', '100%').attr('height', '100%');
  const gZoom = svg.append('g');
  const gLinks = gZoom.append('g').attr('class', 'links');
  const gNodes = gZoom.append('g').attr('class', 'nodes');

  const zoom = d3.zoom().scaleExtent([0.2, 2]).on('zoom', (e) => gZoom.attr('transform', e.transform));
  svg.call(zoom);

  const card = {
    w: 300, h: 96, vGap: 44, hGap: 64,
    render(d) {
      if (d.data.type === 'unit') {
        const level = (d.data.unit_level || 'unit').replace('_', ' ');
        const mgr = d.data.manager_name ? `Manager: ${d.data.manager_name}` : 'Manager: —';
        return `
          <foreignObject x="${-this.w/2}" y="${-this.h/2}" width="${this.w}" height="${this.h}">
            <div xmlns="http://www.w3.org/1999/xhtml"
                 style="width:${this.w}px;height:${this.h}px;padding:12px;
                        display:flex;gap:12px;align-items:center;
                        background:#0f172a;border:1px solid rgba(255,255,255,.18);
                        border-radius:16px;box-shadow:0 2px 6px rgba(0,0,0,.35);">
              <div style="width:48px;height:48px;border-radius:10px;background:#00326E;display:flex;align-items:center;justify-content:center;font-weight:900;color:#fff">
                ${level[0].toUpperCase()}
              </div>
              <div style="min-width:0">
                <div style="font-weight:900;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff">${d.data.name}</div>
                <div style="font-size:12.5px;color:#c5d3e0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${mgr}</div>
              </div>
            </div>
          </foreignObject>`;
      } else {
        const p = d.data;
        const sub = [p.role, p.title, p.department, p.sub_department, p.team].filter(Boolean).join(' • ');
        return `
          <foreignObject x="${-this.w/2}" y="${-this.h/2}" width="${this.w}" height="${this.h}">
            <div xmlns="http://www.w3.org/1999/xhtml"
                 style="width:${this.w}px;height:${this.h}px;padding:12px;
                        display:flex;gap:12px;align-items:center;
                        background:#0f172a;border:1px solid rgba(255,255,255,.12);
                        border-radius:16px;box-shadow:0 2px 6px rgba(0,0,0,.35);">
              <div style="width:48px;height:48px;border-radius:10px;background:#F5821E;display:flex;align-items:center;justify-content:center;font-weight:900;color:#000">
                ${(p.name||'?').charAt(0).toUpperCase()}
              </div>
              <div style="min-width:0">
                <div style="font-weight:800;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff">${p.name||''}</div>
                <div style="font-size:12.5px;color:#c5d3e0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${sub}</div>
              </div>
            </div>
          </foreignObject>`;
      }
    }
  };

  const stratify = d3.stratify().id(d => d.id).parentId(d => d.parentId);
  const root = stratify(nodes);
  root.each(d => (d._children = d.children));
  root.children && root.children.forEach(collapseToDepth);
  function collapseToDepth(d, depth = 1) {
    if (d.depth >= depth && d.children) { d._children = d.children; d.children = null; }
    (d.children || d._children || []).forEach(ch => collapseToDepth(ch, depth));
  }

  function render(centerNode = root) {
    const tree = d3.tree()
      .nodeSize([card.h + card.vGap, card.w + card.hGap])
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.2));
    tree(root);

    const linkGen = d3.linkHorizontal().x(d => d.y).y(d => d.x);
    const link = gLinks.selectAll('path.link').data(root.links(), d => d.target.id);
    link.enter().append('path').attr('class','link').attr('fill','none')
      .attr('stroke','rgba(148,163,184,0.35)').attr('stroke-width',1.2).attr('d',linkGen);
    link.transition().duration(300).attr('d',linkGen);
    link.exit().remove();

    const node = gNodes.selectAll('g.node').data(root.descendants(), d => d.id);
    const nodeEnter = node.enter().append('g').attr('class','node')
      .attr('transform', d => `translate(${d.y},${d.x})`)
      .style('cursor','pointer')
      .on('click', (e,d) => { if(d.children){d._children=d.children; d.children=null;} else {d.children=d._children; d._children=null;} render(d); });

    nodeEnter.append('g').html(d => card.render(d));
    node.transition().duration(300).attr('transform', d => `translate(${d.y},${d.x})`);
    node.exit().remove();
  }

  document.getElementById('expand').onclick = () => { expandAll(root); render(root); };
  document.getElementById('collapse').onclick = () => { collapseToDepth(root, 1); render(root); };
  document.getElementById('fit').onclick = () => { render(root); };
  function expandAll(d){ if(d._children){d.children=d._children; d._children=null;} (d.children||[]).forEach(expandAll); }

  const q = document.getElementById('q');
  q.addEventListener('input', () => {
    const v = (q.value || '').toLowerCase().trim(); if(!v) return;
    const all = root.descendants();
    const match = all.find(n => {
      const x = n.data;
      if (x.type === 'unit') return (x.name||'').toLowerCase().includes(v);
      return [x.name,x.role,x.title,x.department,x.sub_department,x.team]
        .filter(Boolean).some(s => s.toLowerCase().includes(v));
    });
    if (match) {
      let p = match; while (p){ if(p._children){p.children=p._children; p._children=null;} p=p.parent; }
      render(match);
    }
  });

  new ResizeObserver(() => render(root)).observe(container);
  render(root);
})();
