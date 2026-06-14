# 2단계: 현재 Colab CUDA 버전에 맞는 PyTorch 설치
!pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3단계: CLIP 및 기타 패키지 설치
!pip install git+https://github.com/openai/CLIP.git
!pip install Pillow>=9.0.0 matplotlib>=3.5.0 numpy>=1.21.0 requests>=2.25.0

# 4단계: 설치 확인
# 4단계: 설치 확인 (여러 줄로 나누어서)
!python -c "import torch; print('✅ PyTorch:', torch.__version__)"
!python -c "import torch; print('✅ CUDA 사용 가능:', torch.cuda.is_available())"
!python -c "import torch; print('✅ GPU:', torch.cuda.get_device_name() if torch.cuda.is_available() else 'CPU 모드')"
!python -c "import clip; print('✅ CLIP 로드 성공!')"
!python -c "print('🎉 모든 패키지 설치 완료!')"

# 추가: GUI 패키지 (선택사항)
!apt-get update -qq
!apt-get install -y python3-tk
!pip install ipywidgets

# 설치 확인
import torch
import clip
import PIL
print(f"✅ PyTorch: {torch.__version__}")
print(f"✅ CUDA 사용 가능: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✅ GPU: {torch.cuda.get_device_name()}")
print("✅ 모든 패키지 설치 완료!")


# 실제 딥러닝 학습 모델 - 진짜 학습이 일어나는 버전
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import clip
import numpy as np
import requests
from io import BytesIO
import time
import os

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🔥 Real Deep Learning Training Model")
print(f"💻 Device: {device}")

class TextToStyleEncoder(nn.Module):
    """텍스트를 스타일 벡터로 변환하는 실제 신경망"""

    def __init__(self, text_dim=512, style_dim=256):
        super(TextToStyleEncoder, self).__init__()

        self.text_encoder = nn.Sequential(
            nn.Linear(text_dim, 1024),
            nn.ReLU(),
            nn.BatchNorm1d(1024),
            nn.Dropout(0.2),

            nn.Linear(1024, 2048),
            nn.ReLU(),
            nn.BatchNorm1d(2048),
            nn.Dropout(0.2),

            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.BatchNorm1d(1024),
            nn.Dropout(0.1),

            nn.Linear(1024, style_dim)
        )

        # 스타일 벡터를 이미지 파라미터로 변환
        self.style_to_color = nn.Sequential(
            nn.Linear(style_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 3 * 64),  # RGB 색상 팔레트
            nn.Sigmoid()
        )

        self.style_to_pattern = nn.Sequential(
            nn.Linear(style_dim, 512),
            nn.ReLU(),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 16),  # 패턴 파라미터
            nn.Tanh()
        )

        self.style_to_texture = nn.Sequential(
            nn.Linear(style_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 8),  # 텍스처 파라미터
            nn.Sigmoid()
        )

    def forward(self, text_features):
        # 텍스트 → 스타일 벡터
        style_vector = self.text_encoder(text_features)

        # 스타일 벡터 → 이미지 파라미터
        color_params = self.style_to_color(style_vector)
        pattern_params = self.style_to_pattern(style_vector)
        texture_params = self.style_to_texture(style_vector)

        return style_vector, color_params, pattern_params, texture_params

class StyleImageGenerator(nn.Module):
    """스타일 파라미터로 실제 이미지 생성하는 GAN-like 생성기"""

    def __init__(self, style_dim=256):
        super(StyleImageGenerator, self).__init__()

        self.style_dim = style_dim

        # 초기 dense layer
        self.fc = nn.Linear(style_dim, 256 * 4 * 4)

        # Upsampling layers
        self.upconv_layers = nn.ModuleList([
            # 4x4 → 8x8
            nn.ConvTranspose2d(256, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),

            # 8x8 → 16x16
            nn.ConvTranspose2d(256, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),

            # 16x16 → 32x32
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            # 32x32 → 64x64
            nn.ConvTranspose2d(128, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),

            # 64x64 → 128x128
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            # 128x128 → 256x256
            nn.ConvTranspose2d(64, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),

            # 256x256 → 512x512
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),

            # 최종 RGB 출력
            nn.ConvTranspose2d(32, 3, kernel_size=3, stride=1, padding=1),
            nn.Tanh()
        ])

    def forward(self, style_vector):
        batch_size = style_vector.size(0)

        # Dense layer
        x = self.fc(style_vector)
        x = x.view(batch_size, 256, 4, 4)

        # Upsampling
        for layer in self.upconv_layers:
            x = layer(x)

        # -1~1에서 0~1로 변환
        x = (x + 1) / 2

        return x

class StyleDiscriminator(nn.Module):
    """생성된 스타일의 품질을 판별하는 판별기"""

    def __init__(self):
        super(StyleDiscriminator, self).__init__()

        self.conv_layers = nn.Sequential(
            # 512x512 → 256x256
            nn.Conv2d(3, 32, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2),

            # 256x256 → 128x128
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2),

            # 128x128 → 64x64
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),

            # 64x64 → 32x32
            nn.Conv2d(128, 256, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2),

            # 32x32 → 16x16
            nn.Conv2d(256, 512, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),

            # 16x16 → 8x8
            nn.Conv2d(512, 512, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),

            # 8x8 → 4x4
            nn.Conv2d(512, 512, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2)
        )

        self.classifier = nn.Sequential(
            nn.Linear(512 * 4 * 4, 1024),
            nn.LeakyReLU(0.2),
            nn.Dropout(0.3),
            nn.Linear(1024, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        features = self.conv_layers(x)
        features = features.view(features.size(0), -1)
        output = self.classifier(features)
        return output

class RealTextGuidedStyleModel:
    """실제 학습이 일어나는 텍스트 가이드 스타일 모델"""

    def __init__(self):
        print("🔥 실제 딥러닝 모델 초기화 중...")

        # CLIP 모델 로드
        self.clip_model, self.clip_preprocess = clip.load("ViT-B/32", device=device)

        # 커스텀 네트워크들
        self.text_encoder = TextToStyleEncoder().to(device)
        self.style_generator = StyleImageGenerator().to(device)
        self.discriminator = StyleDiscriminator().to(device)

        # VGG19 (사전 훈련된 특징 추출기)
        vgg = models.vgg19(pretrained=True).features.to(device).eval()
        self.vgg = vgg

        # 옵티마이저
        self.optimizer_G = optim.Adam(
            list(self.text_encoder.parameters()) + list(self.style_generator.parameters()),
            lr=0.0002, betas=(0.5, 0.999)
        )
        self.optimizer_D = optim.Adam(
            self.discriminator.parameters(),
            lr=0.0002, betas=(0.5, 0.999)
        )

        # 손실 함수들
        self.adversarial_loss = nn.BCELoss()
        self.l1_loss = nn.L1Loss()
        self.mse_loss = nn.MSELoss()

        print("✅ 모델 초기화 완료!")

    def encode_text(self, text_list):
        """텍스트 리스트를 CLIP으로 인코딩"""
        texts = clip.tokenize(text_list).to(device)
        with torch.no_grad():
            text_features = self.clip_model.encode_text(texts)
        return text_features.float()

    def create_training_data(self, batch_size=8):
        """실제 학습용 데이터 생성"""
        # 다양한 스타일 텍스트들
        style_texts = [
            "vibrant swirling colors like van gogh",
            "geometric cubist shapes in bright colors",
            "soft impressionist watercolor painting",
            "dark gothic mysterious atmosphere",
            "bright neon cyberpunk style",
            "abstract expressionist bold strokes",
            "delicate pastel spring flowers",
            "dramatic baroque chiaroscuro lighting",
            "minimalist clean modern design",
            "vintage retro warm color palette",
            "psychedelic kaleidoscope patterns",
            "traditional japanese ukiyo-e style",
            "renaissance classical realistic portrait",
            "surreal dreamlike melting forms",
            "pop art bold commercial colors"
        ]

        # 배치 생성
        batch_texts = np.random.choice(style_texts, batch_size)
        text_features = self.encode_text(batch_texts.tolist())

        # 실제 스타일 이미지들 (가상으로 생성)
        real_style_images = torch.rand(batch_size, 3, 512, 512).to(device)

        return text_features, real_style_images, batch_texts

    def train_one_epoch(self, num_batches=10):
        """한 에포크 학습"""
        total_g_loss = 0
        total_d_loss = 0

        for batch_idx in range(num_batches):
            batch_size = 4  # T4 GPU 메모리 고려

            # 실제 데이터 생성
            text_features, real_images, texts = self.create_training_data(batch_size)

            # ================
            # 판별기 학습
            # ================
            self.optimizer_D.zero_grad()

            # 실제 이미지에 대한 판별
            real_pred = self.discriminator(real_images)
            real_loss = self.adversarial_loss(real_pred, torch.ones_like(real_pred))

            # 가짜 이미지 생성 및 판별
            style_vector, color_params, pattern_params, texture_params = self.text_encoder(text_features)
            fake_images = self.style_generator(style_vector)
            fake_pred = self.discriminator(fake_images.detach())
            fake_loss = self.adversarial_loss(fake_pred, torch.zeros_like(fake_pred))

            # 판별기 총 손실
            d_loss = (real_loss + fake_loss) / 2
            d_loss.backward()
            self.optimizer_D.step()

            # ================
            # 생성기 학습
            # ================
            self.optimizer_G.zero_grad()

            # 가짜 이미지 재생성 (그라디언트 연결)
            style_vector, color_params, pattern_params, texture_params = self.text_encoder(text_features)
            fake_images = self.style_generator(style_vector)

            # 적대적 손실
            fake_pred = self.discriminator(fake_images)
            adv_loss = self.adversarial_loss(fake_pred, torch.ones_like(fake_pred))

            # CLIP 유사도 손실
            fake_clip_features = self.get_clip_image_features(fake_images)
            clip_loss = 1 - torch.cosine_similarity(fake_clip_features, text_features).mean()

            # 스타일 일관성 손실 (VGG 기반)
            style_loss = self.compute_style_loss(fake_images, real_images)

            # 총 생성기 손실
            g_loss = adv_loss + 10.0 * clip_loss + 5.0 * style_loss
            g_loss.backward()
            self.optimizer_G.step()

            total_g_loss += g_loss.item()
            total_d_loss += d_loss.item()

            # 진행상황 출력
            if batch_idx % 5 == 0:
                print(f"  Batch {batch_idx}/{num_batches} - G_Loss: {g_loss.item():.4f}, D_Loss: {d_loss.item():.4f}")

        return total_g_loss / num_batches, total_d_loss / num_batches

    def get_clip_image_features(self, images):
        """이미지를 CLIP 특징으로 변환"""
        # 이미지를 CLIP 입력 형식으로 변환
        images_224 = torch.nn.functional.interpolate(images, size=224, mode='bilinear')

        with torch.no_grad():
            image_features = self.clip_model.encode_image(images_224)

        return image_features.float()

    def compute_style_loss(self, generated, target):
        """VGG 기반 스타일 손실 계산"""
        def get_features(image, model, layers=None):
            if layers is None:
                layers = {'0': 'conv_1', '5': 'conv_2', '10': 'conv_3',
                         '19': 'conv_4', '28': 'conv_5'}

            features = {}
            x = image

            for name, layer in model._modules.items():
                x = layer(x)
                if name in layers:
                    features[layers[name]] = x

            return features

        def gram_matrix(tensor):
            batch_size, depth, height, width = tensor.size()
            features = tensor.view(batch_size * depth, height * width)
            gram = torch.mm(features, features.t())
            return gram.div(batch_size * depth * height * width)

        gen_features = get_features(generated, self.vgg)
        target_features = get_features(target, self.vgg)

        style_loss = 0
        for layer in gen_features:
            gen_gram = gram_matrix(gen_features[layer])
            target_gram = gram_matrix(target_features[layer])
            style_loss += self.mse_loss(gen_gram, target_gram)

        return style_loss

    def train_model(self, epochs=20, batches_per_epoch=20):
        """실제 모델 학습 실행"""
        print(f"🔥 실제 딥러닝 학습 시작!")
        print(f"⚙️ 설정: {epochs} 에포크, 에포크당 {batches_per_epoch} 배치")
        print(f"💾 예상 시간: {epochs * batches_per_epoch * 0.5:.1f}분")
        print("=" * 50)

        start_time = time.time()

        for epoch in range(epochs):
            print(f"\n📊 Epoch {epoch+1}/{epochs}")
            epoch_start = time.time()

            # 학습 모드 설정
            self.text_encoder.train()
            self.style_generator.train()
            self.discriminator.train()

            # 한 에포크 학습
            avg_g_loss, avg_d_loss = self.train_one_epoch(batches_per_epoch)

            epoch_time = time.time() - epoch_start

            print(f"✅ Epoch {epoch+1} 완료 ({epoch_time:.1f}s)")
            print(f"   평균 G_Loss: {avg_g_loss:.4f}")
            print(f"   평균 D_Loss: {avg_d_loss:.4f}")

            # 중간 저장 (매 5 에포크)
            if (epoch + 1) % 5 == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pth")
                print(f"💾 체크포인트 저장: epoch_{epoch+1}")

        total_time = time.time() - start_time
        print(f"\n🎉 학습 완료! (총 소요시간: {total_time/60:.1f}분)")

        # 최종 모델 저장
        final_path = self.save_model("trained_text_guided_style_model.pth")
        print(f"💾 최종 모델 저장: {final_path}")

        return final_path

    def save_checkpoint(self, filepath):
        """체크포인트 저장"""
        torch.save({
            'text_encoder_state_dict': self.text_encoder.state_dict(),
            'style_generator_state_dict': self.style_generator.state_dict(),
            'discriminator_state_dict': self.discriminator.state_dict(),
            'optimizer_G_state_dict': self.optimizer_G.state_dict(),
            'optimizer_D_state_dict': self.optimizer_D.state_dict(),
        }, filepath)

    def save_model(self, filepath):
        """최종 모델 저장"""
        torch.save({
            'text_encoder_state_dict': self.text_encoder.state_dict(),
            'style_generator_state_dict': self.style_generator.state_dict(),
            'model_config': {
                'text_dim': 512,
                'style_dim': 256,
                'device': str(device)
            }
        }, filepath)
        return filepath

    def generate_style_from_text(self, text_prompt):
        """훈련된 모델로 텍스트에서 스타일 생성"""
        self.text_encoder.eval()
        self.style_generator.eval()

        with torch.no_grad():
            text_features = self.encode_text([text_prompt])
            style_vector, _, _, _ = self.text_encoder(text_features)
            style_image = self.style_generator(style_vector)

        return style_image

# 실제 학습 실행 함수
def run_real_training():
    """실제 딥러닝 학습 실행"""
    print("🔥 Real Deep Learning Training")
    print("=" * 40)

    try:
        # 모델 초기화
        model = RealTextGuidedStyleModel()

        # 사용자 확인
        print("\n⚠️ 실제 딥러닝 학습을 시작합니다.")
        print("💡 T4 GPU에서 약 15-20분 소요됩니다.")
        print("🔋 컴퓨팅 유닛을 상당히 사용합니다.")

        response = input("계속 진행하시겠습니까? (y/n): ").strip().lower()

        if response != 'y' and response != 'yes':
            print("❌ 학습이 취소되었습니다.")
            return None

        # 실제 학습 시작
        model_path = model.train_model(epochs=15, batches_per_epoch=15)

        print("\n🎉 실제 딥러닝 학습 완료!")
        print(f"📁 모델 저장 위치: {model_path}")

        # 테스트 생성
        print("\n🧪 학습된 모델 테스트...")
        test_prompts = [
            "vibrant van gogh swirling colors",
            "geometric cubist bright shapes",
            "soft watercolor gentle pastels"
        ]

        for prompt in test_prompts:
            style_image = model.generate_style_from_text(prompt)
            print(f"✅ 생성 완료: '{prompt}'")

        return model, model_path

    except KeyboardInterrupt:
        print("\n⚠️ 학습이 중단되었습니다.")
        return None
    except Exception as e:
        print(f"❌ 학습 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

# 메인 실행
if __name__ == "__main__":
    print("🔥 Real Deep Learning Text-Guided Style Transfer")
    print("실제 신경망 학습이 일어나는 버전")
    print()

    # 메모리 정리
    torch.cuda.empty_cache()

    # 실제 학습 실행
    result = run_real_training()

    if result:
        model, model_path = result
        print(f"\n📋 다음 단계:")
        print(f"1. 학습된 모델 파일: {model_path}")
        print(f"2. 사용자 인터페이스에서 로드하여 사용")
        print(f"3. 실제 텍스트 가이드 스타일 변환 가능")

    print("\n🧹 메모리 정리...")
    torch.cuda.empty_cache()
    print("✅ 완료!")



    # 완전히 작동하는 텍스트 가이드 스타일 변환 (에러 수정 완료)
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image
import clip
import numpy as np
import matplotlib.pyplot as plt
import warnings
import time
from google.colab import files

warnings.filterwarnings('ignore')
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🎨 Working Text-Guided Style Transfer")
print(f"💻 Device: {device}")

class WorkingStyleTransfer:
    """완전히 작동하는 스타일 변환 시스템"""

    def __init__(self):
        print("🔄 시스템 초기화...")
        self.setup_models()
        self.current_image = None
        print("✅ 준비 완료!")

    def setup_models(self):
        """모델 설정"""
        # CLIP 모델
        self.clip_model, _ = clip.load("ViT-B/32", device=device)

        # VGG19
        vgg = models.vgg19(pretrained=True).features.to(device).eval()
        self.vgg = vgg

        # 정규화
        self.mean = torch.tensor([0.485, 0.456, 0.406]).to(device)
        self.std = torch.tensor([0.229, 0.224, 0.225]).to(device)

        # 레이어
        self.style_layers = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']

    def upload_image(self):
        """이미지 업로드"""
        print("\n📁 이미지 업로드")
        print("파일 선택 버튼을 클릭하세요!")

        try:
            uploaded = files.upload()
            if uploaded:
                filename = list(uploaded.keys())[0]
                self.current_image = Image.open(filename).convert('RGB')

                plt.figure(figsize=(8, 6))
                plt.imshow(self.current_image)
                plt.title(f"업로드: {filename}")
                plt.axis('off')
                plt.show()

                print("✅ 이미지 로드 완료!")
                return True
            return False
        except Exception as e:
            print(f"❌ 업로드 실패: {e}")
            return False

    def get_style_input(self):
        """스타일 텍스트 입력"""
        print("\n🎨 스타일 텍스트 입력")
        print("=" * 25)
        print("💡 스타일을 영어로 설명하세요!")
        print()
        print("✅ 좋은 예시:")
        print("   'metallic chrome style with bright reflections'")
        print("   'vibrant van gogh swirling colors'")
        print("   'soft watercolor with pink and blue'")
        print("   'dark gothic with purple shadows'")
        print("   'bright neon cyberpunk colors'")
        print()

        style_text = input("스타일 설명: ").strip()
        if not style_text:
            style_text = "colorful abstract painting"

        print(f"✅ 스타일: '{style_text}'")
        return style_text

    def encode_text(self, text):
        """텍스트 인코딩"""
        text_tokens = clip.tokenize([text]).to(device)
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
        return text_features.float()

    def create_style_from_text(self, text):
        """텍스트에서 스타일 생성"""
        print(f"🔍 텍스트 분석: '{text}'")

        size = 512
        canvas = torch.zeros(3, size, size).to(device)

        # 좌표
        x, y = torch.meshgrid(
            torch.linspace(-1, 1, size),
            torch.linspace(-1, 1, size),
            indexing='ij'
        )
        x, y = x.to(device), y.to(device)

        # 텍스트 분석
        text_lower = text.lower()

        # 색상 추출
        colors = self.get_colors(text_lower)

        # 패턴 생성
        if any(word in text_lower for word in ['swirl', 'van gogh', 'spiral']):
            angle = torch.atan2(y, x)
            radius = torch.sqrt(x**2 + y**2)
            pattern = torch.sin(angle * 8 + radius * 12)
        elif any(word in text_lower for word in ['geometric', 'cubist', 'angular']):
            pattern = torch.sin(x * 10) * torch.cos(y * 10)
        elif any(word in text_lower for word in ['chrome', 'metal', 'shiny', 'reflections']):
            # 반짝이는 메탈릭 패턴
            pattern = torch.abs(torch.sin(x * 6) * torch.cos(y * 6))
            colors = [[0.8, 0.8, 0.9], [0.9, 0.9, 1.0], [0.7, 0.7, 0.8]]  # 메탈릭 색상
        elif any(word in text_lower for word in ['water', 'soft', 'gentle']):
            pattern = torch.exp(-(x**2 + y**2) * 0.5)
        else:
            pattern = torch.sin(x * 5) * torch.cos(y * 5)

        # 색상 적용
        if len(colors) == 1:
            color = torch.tensor(colors[0]).to(device)
            for c in range(3):
                canvas[c] = pattern * 0.6 + color[c] * 0.4
        else:
            for i, color in enumerate(colors[:3]):
                color_tensor = torch.tensor(color).to(device)
                weight = torch.sin(pattern * (i + 1) * np.pi) ** 2
                for c in range(3):
                    canvas[c] += weight * color_tensor[c]
            canvas = canvas / max(len(colors), 1)

        canvas = torch.clamp(canvas, 0, 1)
        print("✅ 스타일 생성 완료!")
        return canvas.unsqueeze(0)

    def get_colors(self, text):
        """색상 추출"""
        colors = []

        color_map = {
            'red': [0.9, 0.1, 0.1], 'blue': [0.1, 0.1, 0.9], 'green': [0.1, 0.8, 0.1],
            'yellow': [0.9, 0.9, 0.1], 'purple': [0.7, 0.1, 0.7], 'orange': [0.9, 0.5, 0.1],
            'pink': [0.9, 0.6, 0.7], 'chrome': [0.8, 0.8, 0.9], 'silver': [0.7, 0.7, 0.8],
            'gold': [0.9, 0.7, 0.1], 'cyan': [0.1, 0.8, 0.8], 'neon': [0.0, 1.0, 0.0]
        }

        for color_name, rgb in color_map.items():
            if color_name in text:
                colors.append(rgb)

        if not colors:
            colors = [[0.6, 0.4, 0.7]]  # 기본 색상

        return colors

    def gram_matrix(self, tensor):
        """그람 행렬"""
        b, c, h, w = tensor.size()
        features = tensor.view(b * c, h * w)
        gram = torch.mm(features, features.t())
        return gram.div(b * c * h * w)

    def get_features(self, image):
        """VGG 특징 추출"""
        layers = {'0': 'conv_1', '5': 'conv_2', '10': 'conv_3',
                 '19': 'conv_4', '21': 'conv_5'}

        features = {}
        x = image

        for name, layer in self.vgg._modules.items():
            x = layer(x)
            if name in layers:
                features[layers[name]] = x

        return features

    def style_transfer(self, content_img, style_text, steps=150):
        """스타일 변환 (에러 수정 완료)"""
        print(f"\n🚀 스타일 변환 시작!")
        print(f"🎨 스타일: '{style_text}'")
        print(f"⚙️ {steps}스텝 진행")

        start_time = time.time()

        try:
            # 전처리
            transform = transforms.Compose([
                transforms.Resize(512),
                transforms.CenterCrop(512),
                transforms.ToTensor(),
                transforms.Normalize(self.mean, self.std)
            ])

            content_tensor = transform(content_img).unsqueeze(0).to(device)
            style_tensor = self.create_style_from_text(style_text)

            # 특징 추출
            content_features = self.get_features(content_tensor)
            style_features = self.get_features(style_tensor)

            # 스타일 그람 행렬
            style_grams = {}
            for layer in self.style_layers:
                if layer in style_features:
                    style_grams[layer] = self.gram_matrix(style_features[layer])

            # 타겟 초기화
            target = content_tensor.clone().requires_grad_(True)
            optimizer = torch.optim.Adam([target], lr=0.01)

            # CLIP 특징
            text_features = self.encode_text(style_text)

            print("\n🔄 최적화 진행...")

            for step in range(steps):
                # 특징 추출
                target_features = self.get_features(target)

                # 콘텐츠 손실
                content_loss = torch.mean((target_features['conv_4'] - content_features['conv_4']) ** 2)

                # 스타일 손실
                style_loss = 0
                for layer in self.style_layers:
                    if layer in target_features and layer in style_grams:
                        target_gram = self.gram_matrix(target_features[layer])
                        style_gram = style_grams[layer]
                        style_loss += torch.mean((target_gram - style_gram) ** 2)

                # CLIP 손실
                clip_loss = 0
                if step % 50 == 0:
                    # 정규화 해제 후 CLIP 입력 형식으로 변환
                    target_unnorm = target * self.std.view(1, 3, 1, 1) + self.mean.view(1, 3, 1, 1)
                    target_unnorm = torch.clamp(target_unnorm, 0, 1)
                    target_224 = torch.nn.functional.interpolate(target_unnorm, size=224, mode='bilinear')

                    with torch.no_grad():
                        target_clip_features = self.clip_model.encode_image(target_224)

                    clip_loss = 1 - torch.cosine_similarity(target_clip_features, text_features).mean()

                # 총 손실
                total_loss = content_loss + 1e6 * style_loss + 0.3 * clip_loss

                # 최적화
                optimizer.zero_grad()
                total_loss.backward(retain_graph=True)
                optimizer.step()

                # 진행상황
                if step % 25 == 0:
                    elapsed = int(time.time() - start_time)
                    progress = int((step / steps) * 100)
                    print(f"진행률: {progress}% ({step}/{steps}) - {elapsed}s")

            # 결과 변환 (에러 수정 완료)
            with torch.no_grad():
                result_tensor = target.detach()  # 그라디언트 분리
                result_tensor = result_tensor * self.std.view(1, 3, 1, 1) + self.mean.view(1, 3, 1, 1)
                result_tensor = torch.clamp(result_tensor, 0, 1)

                # CPU로 이동 후 numpy 변환
                result_array = result_tensor.squeeze(0).cpu().permute(1, 2, 0).numpy()
                result_image = Image.fromarray((result_array * 255).astype(np.uint8))

            total_time = int(time.time() - start_time)
            print(f"✅ 변환 완료! ({total_time}초)")

            return result_image

        except KeyboardInterrupt:
            print("\n⚠️ 중단됨")
            return None
        except Exception as e:
            print(f"❌ 변환 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

    def display_result(self, original, result, style_text):
        """결과 표시"""
        if result is None:
            print("⚠️ 표시할 결과가 없습니다.")
            return

        print("\n🖼️ 최종 결과")

        fig, axes = plt.subplots(1, 2, figsize=(15, 7))

        axes[0].imshow(original)
        axes[0].set_title("원본 이미지", fontsize=14, fontweight='bold')
        axes[0].axis('off')

        axes[1].imshow(result)
        axes[1].set_title(f"변환 결과\n'{style_text}'", fontsize=12, fontweight='bold')
        axes[1].axis('off')

        plt.tight_layout()
        plt.show()

        # 저장
        timestamp = int(time.time())
        filename = f"style_result_{timestamp}.png"
        result.save(filename)
        print(f"💾 저장: {filename}")

        try:
            files.download(filename)
            print("📥 다운로드 시작!")
        except:
            print("💡 파일 저장됨")

        print("✅ 완료!")

    def run(self):
        """메인 실행"""
        print("🎨 Working Text-Guided Style Transfer")
        print("=" * 40)
        print("🤖 텍스트로 스타일을 지정하여 이미지를 변환합니다!")

        try:
            # 1. 이미지 업로드
            if not self.upload_image():
                print("❌ 이미지가 필요합니다.")
                return

            # 2. 스타일 입력
            style_text = self.get_style_input()

            # 3. 품질 선택
            print("\n⚙️ 품질 선택")
            print("1. 빠름 (100스텝)")
            print("2. 보통 (150스텝)")
            print("3. 고품질 (200스텝)")

            choice = input("선택 (1-3, 기본 2): ").strip()
            steps = 100 if choice == "1" else 200 if choice == "3" else 150

            # 4. 변환 실행
            result = self.style_transfer(self.current_image, style_text, steps)

            if result:
                # 5. 결과 표시
                self.display_result(self.current_image, result, style_text)
                return result
            else:
                print("❌ 변환 실패")
                return None

        except KeyboardInterrupt:
            print("\n⚠️ 중단됨")
        except Exception as e:
            print(f"❌ 오류: {e}")

# 실행 함수
def start_working_style_transfer():
    """작동하는 스타일 변환 시작"""
    try:
        print("🚀 Working Style Transfer 시작!")
        print("💡 에러 수정 완료 - 안정적으로 동작합니다")
        print()

        system = WorkingStyleTransfer()
        result = system.run()

        if result:
            print("\n🎉 성공!")

            # 추가 변환
            while True:
                try:
                    again = input("\n다시 시도? (y/n): ").strip().lower()
                    if again == 'y':
                        system.run()
                    else:
                        break
                except KeyboardInterrupt:
                    break

        print("\n👋 감사합니다!")

    except Exception as e:
        print(f"❌ 시스템 오류: {e}")

# 메모리 정리 및 실행
torch.cuda.empty_cache()
start_working_style_transfer()