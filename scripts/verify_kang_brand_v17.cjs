'use strict';
// RE:LAND v17: verify every episode resolves its own scene while the approved portrait stays locked.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const read = file => fs.readFileSync(path.join(root, file), 'utf8');
const dataWindow = {};
vm.runInNewContext(read('kang_blog/data.js'), {window: dataWindow});
assert.equal(dataWindow.KANG_DATA.lectures.length, 60, 'expect exactly 60 courses');
const photoWindow = {KANG_DATA:dataWindow.KANG_DATA};
vm.runInNewContext(read('kang_blog/story-photo-v14.js'), {
  window: photoWindow, URLSearchParams,
  location: {pathname:'/kang/',search:''},
  document: {readyState:'loading',addEventListener(){}},
});
const destinations=new Set();
for(let id=1;id<=60;id++){
  const nodes=new Map();
  const el=sel=>{
    if(!nodes.has(sel))nodes.set(sel,{
      tagName:'IMG',dataset:{},style:{},src:'',alt:'',innerHTML:'',textContent:'',
      removeAttribute(){},setAttribute(){},addEventListener(){},
    });
    return nodes.get(sel);
  };
  const doc={querySelector:el,readyState:'complete',title:''};
  vm.runInNewContext(read('kang_blog/lesson-v6.js'),{
    window:photoWindow, document:doc, URL,URLSearchParams,
    location:{pathname:'/kang/lesson-v6.html',search:'?id='+id}
  },{timeout:1000});
  const course=photoWindow.KANG_DATA.lectures[id-1];
  const hero=el('#lectureImage'), scene=el('#storySceneImage');
  const expected='/kang/assets/lessons/lesson-'+String(id).padStart(3,'0')+'.webp';
  assert.equal(hero.src,'/kang/assets/kang-class-hero-v5.webp', 'brand on '+id);
  assert.equal(hero.dataset.brandHero,'1', 'approved branding locked '+id);
  assert.equal(scene.src,expected,'story photo on '+id);
  assert.equal(scene.dataset.lessonMediaId,String(id),'correct image fallback id '+id);
  assert.equal(el('#storySceneTitle').textContent, course.title,'story caption on '+id);
  assert.match(el('#storySceneEyebrow').textContent,new RegExp('제'+id+'강'));
  assert.match(doc.title,new RegExp(course.title.slice(0,5)));
  destinations.add(scene.src);
}
assert.equal(destinations.size,60,'60 distinct scene photo references');
console.log('PASS: approved master hero + 60 distinct contextual photo references + 60 titles');
