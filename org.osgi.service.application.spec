Name:		org.osgi.service.application
Version:	1.1.0
Release:	1
Summary:	OSGi Application Admin API
Group:		Development/Java
License:	ASL 2.0
URL:		https://docs.osgi.org/
Source0:	https://repo1.maven.org/maven2/org/osgi/org.osgi.service.application/%{version}/org.osgi.service.application-%{version}-sources.jar

BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildRequires:	mvn(org.osgi:osgi.core)
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
OSGi Application Admin 1.1. Application descriptors, handles, schedules,
and the admin permission. Filter, FrameworkUtil, Constants, and
InvalidSyntaxException come from OSGi Core. The package version is 1.1.
This build targets Java 8.

%prep
%setup -q -c -T
# The builders' rpmuncompress passes a sources jar to tar.
python - %{SOURCE0} <<'PY'
import sys
import zipfile
zipfile.ZipFile(sys.argv[1]).extractall(".")
PY
rm -rf META-INF
mkdir -p src/main/java src/main/resources/org/osgi/service/application
mv org src/main/java/
mv src/main/java/org/osgi/service/application/packageinfo src/main/resources/org/osgi/service/application/packageinfo
python - <<'PY'
from pathlib import Path

root = Path("src/main/java/org/osgi/service/application")
names = sorted(path.name for path in root.glob("*.java"))
expect = [
    "ApplicationAdminPermission.java",
    "ApplicationDescriptor.java",
    "ApplicationException.java",
    "ApplicationHandle.java",
    "ScheduledApplication.java",
    "package-info.java",
]
if names != expect:
    raise SystemExit("java files " + " ".join(names))
info = Path("src/main/resources/org/osgi/service/application/packageinfo").read_bytes()
if info != b"version 1.1\n":
    raise SystemExit("packageinfo " + repr(info))
if list(Path("src/main/java").rglob("packageinfo")):
    raise SystemExit("packageinfo still beside the sources")
if "Apache License" not in Path("LICENSE").read_text(encoding="utf-8"):
    raise SystemExit("LICENSE is not the Apache license")
if not Path("about.html").is_file():
    raise SystemExit("missing about.html")
if list(Path(".").rglob("*.jar")) or list(Path(".").rglob("*.class")):
    raise SystemExit("prebuilt binary remains")
for pom in Path(".").rglob("pom.xml"):
    pom.unlink()

Path("pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.osgi</groupId>
  <artifactId>org.osgi.service.application</artifactId>
  <version>%{version}</version>
  <packaging>jar</packaging>
  <name>org.osgi:org.osgi.service.application</name>
  <description>OSGi Application Admin.</description>
  <url>https://docs.osgi.org/</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.release>8</maven.compiler.release>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.osgi</groupId>
      <artifactId>osgi.core</artifactId>
      <version>6.0.0</version>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.12.1</version>
        <configuration>
          <release>8</release>
        </configuration>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.3.0</version>
      </plugin>
    </plugins>
  </build>
</project>
""", encoding="utf-8")
pom = Path("pom.xml").read_text(encoding="utf-8")
for needle in (
    "<artifactId>org.osgi.service.application</artifactId>",
    "<artifactId>osgi.core</artifactId>",
    "<version>6.0.0</version>",
    "<version>%{version}</version>",
    "<release>8</release>",
    "</project.build.sourceEncoding>",
):
    if needle not in pom:
        raise SystemExit("pom missing " + needle)
for needle in ("junit", "SNAPSHOT", "<source>", "<target>", "<parent>", "felix", "maven-bundle-plugin", "osgi.annotation", "<scope>", "projectbuild.sourceEncoding"):
    if needle in pom:
        raise SystemExit("pom still contains " + needle)
PY

%build -a
java --module-path target/org.osgi.service.application-%{version}.jar --describe-module org.osgi.service.application > module-describe.txt
grep -q '^org.osgi.service.application' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q ' automatic$' module-describe.txt || { cat module-describe.txt; exit 1; }
python - <<'PY'
import zipfile
from pathlib import Path
jar = Path("target/org.osgi.service.application-%{version}.jar")
with zipfile.ZipFile(jar) as zf:
    names = set(zf.namelist())
    info = zf.read("org/osgi/service/application/packageinfo")
required = {
    "org/osgi/service/application/ApplicationAdminPermission.class",
    "org/osgi/service/application/ApplicationAdminPermission$SignerWrapper.class",
    "org/osgi/service/application/ApplicationDescriptor.class",
    "org/osgi/service/application/ApplicationDescriptor$Delegate.class",
    "org/osgi/service/application/ApplicationDescriptor$Delegate$1.class",
    "org/osgi/service/application/ApplicationDescriptor$Delegate$2.class",
    "org/osgi/service/application/ApplicationException.class",
    "org/osgi/service/application/ApplicationHandle.class",
    "org/osgi/service/application/ApplicationHandle$Delegate.class",
    "org/osgi/service/application/ApplicationHandle$Delegate$1.class",
    "org/osgi/service/application/ApplicationHandle$Delegate$2.class",
    "org/osgi/service/application/ScheduledApplication.class",
}
missing = sorted(required - names)
if missing:
    raise SystemExit("missing " + " ".join(missing))
# Java 27 emits package-info.class even when the source has no annotations.
if info != b"version 1.1\n":
    raise SystemExit("jar packageinfo " + repr(info))
PY

%files -f .mfiles
%doc LICENSE about.html
