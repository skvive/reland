'use strict';
/* Original AI generated 16:9 photorealistic editorial assets approved for fictional education use. No real site or identifiable official depicted. */
(()=>{
 const photos=Object.freeze({
  "1": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/fcf2c8d6-30f5-465c-9d37-0cebd50376f8.png",
  "2": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/08bb15a1-f888-494f-b893-65499b6cd8cf.png",
  "3": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/fe3862d6-5797-441b-9b78-04cffcd1611d.png",
  "4": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/ab797dde-a3ec-40df-ad8b-91feb669565e.png",
  "5": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/4c7cdde5-3956-4e30-9ea5-41f2d64397b3.png",
  "6": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/9db17342-3ca0-4281-8691-0e059c4048f3.png",
  "7": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/019d83e3-4c23-4584-8d40-e43452de928a.png",
  "8": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/7d429545-b503-4b30-8aa6-5880ba81085e.png",
  "9": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/82b37435-ba9a-4f97-96d6-75f9fa991fb6.png",
  "10": "https://d2ol7oe51mr4n9.cloudfront.net/user_3HQYBhFdk9zQhjBPuuu0mHjev2G/3a502249-10f2-4954-bbb4-3e45360cd943.png"
});
 const captions=Object.freeze({
  "1": "두 시점의 분담금 통지를 비교하는 가족",
  "2": "노후 주택 두 필지의 평가 조건 대조",
  "3": "비례율 계산과 사업수입·비용의 관계",
  "4": "공사비 변경계약과 공사현장",
  "5": "계약금·중도금·잔금 납부 일정",
  "6": "주민 대화방 소문과 정식 문서",
  "7": "총회 안건지와 회의록 대조",
  "8": "총회 출석·의결 정족수 확인",
  "9": "조합장 해임 논란 속 두 공고문",
  "10": "용역비 변경과 조합 회계 장부"
});
 window.KANG_STORY_PHOTO_V14=photos;
 window.KANG_STORY_PHOTO_CAPTIONS_V14=captions;
 const match=location.pathname.match(/\/kang\/lectures\/lesson-(\d{3})\.html$/);
 const apply=()=>{if(!match)return;const id=Number(match[1]),el=document.querySelector('.rk-story img');if(!photos[id]||!el)return;el.src=photos[id];el.alt=captions[id]+' — 가상 학습장면으로 생성된 이미지';el.decoding='async';el.dataset.photoVersion='14';};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply,{once:true});else apply();
})();
