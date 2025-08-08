#!/bin/bash

echo "🚀 Kuma TestFlight Deployment Script"
echo "===================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1 successful${NC}"
    else
        echo -e "${RED}❌ $1 failed${NC}"
        exit 1
    fi
}

# 1. Clean and get dependencies
echo -e "\n${YELLOW}📧 Step 1: Cleaning project...${NC}"
flutter clean
check_status "Flutter clean"

echo -e "\n${YELLOW}📦 Step 2: Getting dependencies...${NC}"
flutter pub get
check_status "Flutter pub get"

# 2. iOS specific setup
echo -e "\n${YELLOW}🍎 Step 3: iOS setup...${NC}"
cd ios
pod install
check_status "Pod install"
cd ..

# 3. Build iOS release
echo -e "\n${YELLOW}🔨 Step 4: Building iOS release...${NC}"
flutter build ios --release
check_status "iOS build"

# 4. Open Xcode
echo -e "\n${YELLOW}📱 Step 5: Opening Xcode...${NC}"
open ios/Runner.xcworkspace

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "\n${YELLOW}Next steps in Xcode:${NC}"
echo "1. Select 'Any iOS Device' as target"
echo "2. Product → Archive"
echo "3. In Organizer: Distribute App → App Store Connect"
echo "4. Follow the upload wizard"

echo -e "\n${YELLOW}TestFlight Setup:${NC}"
echo "1. Go to App Store Connect"
echo "2. Select your app → TestFlight tab"
echo "3. Add test information"
echo "4. Add internal/external testers"
echo "5. Submit for review (external testers only)"

echo -e "\n${GREEN}Good luck with your deployment! 🎉${NC}"