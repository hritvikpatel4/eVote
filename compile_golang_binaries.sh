#!/usr/bin/env bash

cd golang_requests
rm -rf binaries/

package_name=$1
if [ -z $package_name ]
then
    echo "Usage: $0 <package-name>"
    exit 1
fi

# https://golang.org/doc/install/source#environment
platforms=(
    # "aix/ppc64"
    # "android/386"
    # "android/amd64"
    # "android/arm"
    # "android/arm64"
    "darwin/amd64"
    "darwin/arm64"
    # "dragonfly/amd64"
    # "freebsd/386"
    # "freebsd/amd64"
    # "freebsd/arm"
    # "illumos/amd64"
    # "ios/arm64"
    # "js/wasm"
    "linux/386"
    "linux/amd64"
    "linux/arm"
    "linux/arm64"
    # "linux/ppc64"
    # "linux/ppc64le"
    # "linux/mips"
    # "linux/mipsle"
    # "linux/mips64"
    # "linux/mips64le"
    # "linux/riscv64"
    # "linux/s390x"
    # "netbsd/386"
    # "netbsd/amd64"
    # "netbsd/arm"
    # "openbsd/386"
    # "openbsd/amd64"
    # "openbsd/arm"
    # "openbsd/arm64"
    # "plan9/386"
    # "plan9/amd64"
    # "plan9/arm"
    # "solaris/amd64"
    "windows/386"
    "windows/amd64"
)

for platform in "${platforms[@]}"
do
    platform_split=(${platform//\// })
    GOOS=${platform_split[0]}
    GOARCH=${platform_split[1]}
    output_name=$package_name'-'$GOOS'-'$GOARCH
    
    if [ $GOOS == "windows" ]; then
        output_name+='.exe'
    fi

    env GOOS=$GOOS GOARCH=$GOARCH go build -o ./binaries/$output_name $package
    
    if [ $? -ne 0 ]; then
        echo 'An error has occurred! Aborting the script execution...'
        exit 1
    fi
done

cd ..
printf "\n\tDone! Find all the compiled binaries in $(pwd)/golang_requests/binaries\n\n"

sudo chmod +x $(pwd)/golang_requests/binaries/*
