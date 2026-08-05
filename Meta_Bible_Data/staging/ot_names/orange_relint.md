# Vietnamese OT Orange Relint

Relinted existing `staging/ot_names/*_flags.csv` orange rows against current `staging/ot_torah/GOI_Bible_vi` text.

Important: these orange rows are driven by VIE1934 expected-name occurrences, not directly by Hebrew source-name occurrences. A missing expected VIE1934 name can be correct when Hebrew uses a pronoun or when GOI_vi intentionally follows the Hebrew source more tightly.

## Counts

- Raw orange rows relinted: 59
- Unique book/chapter/verse/name rows: 57
- Duplicate overlap rows: 2

### Raw Status Counts

- cleared_case_only: 2
- cleared_loose_orthography: 1
- still_missing_or_source_policy: 56

### Unique Status Counts

- cleared_case_only: 2
- cleared_loose_orthography: 1
- still_missing_or_source_policy: 54

### Unique Counts By Book

- GEN: cleared_case_only=2, cleared_loose_orthography=1, still_missing_or_source_policy=4
- EXO: still_missing_or_source_policy=10
- LEV: still_missing_or_source_policy=3
- NUM: still_missing_or_source_policy=27
- DEU: still_missing_or_source_policy=10

## Non-Missing Rows

- GEN 29:28 `Lê-a` -> cleared_loose_orthography
- GEN 36:38 `Ba-anh-Ha-nan` -> cleared_case_only
- GEN 36:39 `Ba-anh-Ha-nan` -> cleared_case_only

## Remaining Unique Rows

- DEU 2:21 expected `Am-môn`: Dân đó là một dân lớn, mạnh và cao lớn như dân A-na-kim; nhưng Đức Giê-hô-va đã tiêu diệt chúng khỏi trước mặt chúng, và chúng chiếm lấy đất ấy rồi ở đó thay thế chúng.
- DEU 2:21 expected `Rê-pha-im`: Dân đó là một dân lớn, mạnh và cao lớn như dân A-na-kim; nhưng Đức Giê-hô-va đã tiêu diệt chúng khỏi trước mặt chúng, và chúng chiếm lấy đất ấy rồi ở đó thay thế chúng.
- DEU 4:15 expected `Đức Chúa Trời`: Vậy, các ngươi hãy giữ gìn rất cẩn thận lấy mạng sống mình, vì các ngươi không thấy hình dạng nào hết trong ngày Đức Giê-hô-va phán cùng các ngươi tại Hô-rếp từ giữa ngọn lửa.
- DEU 9:4 expected `Đức Chúa Trời`: Chớ nói trong lòng ngươi rằng: Vì cớ sự công bình của ta mà Đức Giê-hô-va đã dẫn ta vào để chiếm lấy đất nầy; nhưng chính vì sự gian ác của các dân tộc đó mà Đức Giê-hô-va đuổi chúng nó ra khỏi trước mặt ngươi.
- DEU 10:7 expected `Y-sơ-ra-ên`: Từ đó, họ đi đến Gút-gô-đa, rồi từ Gút-gô-đa đến Dốt-ba-tha, là đất có các suối nước.
- DEU 13:17 expected `Đức Chúa Trời`: Chớ để điều gì đáng bị tiêu diệt dính lại trong tay ngươi, hầu cho Đức Giê-hô-va sẽ nguôi cơn thạnh nộ, và sẽ thương xót ngươi, thương yêu ngươi, và làm cho ngươi sinh sôi nảy nở, như Ngài đã thề cùng tổ phụ ngươi.
- DEU 24:9 expected `Đức Chúa Trời`: Hãy nhớ điều Đức Giê-hô-va đã làm cho Mi-ri-am dọc đường khi các ngươi ra khỏi Ai Cập.
- DEU 28:14 expected `Đức Giê-hô-va`: và ngươi sẽ không đi lạc khỏi mọi điều phán mà ta truyền cho các ngươi ngày nay, không chếch sang bên phải hay bên trái, để đi theo và phục sự các thần khác
- DEU 32:43 expected `Đức Chúa Trời`: Hỡi các nước, hãy reo vui cùng dân Ngài, vì Đức Giê-hô-va sẽ báo thù huyết của tôi tớ Ngài, và báo sự báo thù cho kẻ thù nghịch Ngài, và sẽ làm cho đất Ngài được xá tội cho dân Ngài.
- DEU 33:9 expected `Lê-vi`: Người nói cùng cha mình: Ta chẳng thấy cha; cùng mẹ mình: Ta không biết mẹ; chẳng nhận anh em mình, chẳng biết con cái mình; vì họ giữ lời Đức Giê-hô-va, và gìn giữ giao ước Ngài.
- EXO 1:11 expected `Y-sơ-ra-ên`: Họ đặt những người cai trị lao dịch trên dân ấy, để hành hạ họ bằng những công việc nặng nhọc; và họ xây các thành kho tàng cho Pha-ra-ôn là Phi-thom và Ram-se.
- EXO 2:22 expected `Môi-se`: Sinh một trai, đặt tên là Ghẹt-sôn, vì nói rằng: Tôi là kẻ khách lạ tại đất ngoại bang.
- EXO 4:24 expected `Môi-se`: Dọc đường, tại một nơi nghỉ ngơi, Đức Giê-hô-va gặp gỡ người, và tìm cách giết ông.
- EXO 4:26 expected `Đức Giê-hô-va`: Ngài bèn buông tha người ấy; lúc ấy nàng nói: Chồng bằng máu, vì cớ các phép cắt bì.
- EXO 6:1 expected `Y-sơ-ra-ên`: Đức Giê-hô-va phán cùng Môi-se rằng: Bây giờ ngươi sẽ thấy điều ta sẽ làm cho Pha-ra-ôn; vì nhờ tay quyền năng, người ấy sẽ thả họ, và nhờ tay quyền năng, người ấy sẽ đuổi họ ra khỏi đất nước mình.
- EXO 14:17 expected `Y-sơ-ra-ên`: Và chính Ta đây, Ta sẽ làm cho lòng dân Ê-díp-tô trở nên cứng cỏi, khiến chúng đuổi theo sau họ; và Ta sẽ được tôn vinh nơi Pha-ra-ôn cùng toàn thể đạo binh của người, trong các xe chiến của người và các kỵ binh của n...
- EXO 14:28 expected `Y-sơ-ra-ên`: Nước trở lại, phủ kín xe và kỵ binh, toàn thể đạo binh của Pha-ra-ôn đã theo sau họ xuống biển; chẳng còn sót lại một người nào trong số họ.
- EXO 24:1 expected `Đức Chúa Trời`: Đức Giê-hô-va phán cùng Môi-se rằng: Ngươi và A-rôn, Na-đáp, A-bi-hu cùng bảy mươi trưởng lão Y-sơ-ra-ên hãy lên cùng Đức Giê-hô-va; các ngươi sẽ thờ lạy từ xa.
- EXO 27:12 expected `Bố-vi`: Bề rộng của hành lang về phía tây là năm mươi thước, mười cây trụ và mười đế trụ.
- EXO 32:18 expected `Môi-se`: Không phải tiếng reo hò chiến thắng, cũng không phải tiếng kêu than thất bại; ấy là tiếng hát mà tôi đang nghe.
- GEN 8:9 expected `Nô-ê`: Bồ câu không tìm được chỗ nào cho bàn chân nó đậu, nên bay trở lại với ông trong tàu, vì nước còn phủ khắp mặt đất. Ông đưa tay ra, bắt lấy nó, rồi đưa nó vào tàu với mình.
- GEN 25:11 expected `Đức Giê-hô-va`: Sau khi Aùp-ra-ham qua đời, Đức Chúa Trời ban phước cho Y-sác con trai người. Y-sác ở gần bên giếng La-chai-Roi.
- GEN 35:18 expected `Ra-chên`: Khi mạng sống của nàng ra đi vì nàng chết, thì nàng đặt tên con trai là Bê-nô-ni; nhưng cha nó đặt tên cho nó là Bên-gia-min.
- GEN 37:36 expected `Giô-sép`: Các người Ma-đi-an đã bán chàng cho người Ai-cập, là Phô-ti-pha, hoạn quan của Pha-ra-ôn, quản gia các đầu bếp.
- LEV 24:12 expected `Sê-lô-mít`: Họ giam ông tại nơi giam giữ để Đức Giê-hô-va phán dạy họ.
- LEV 24:12 expected `Điệp-ri`: Họ giam ông tại nơi giam giữ để Đức Giê-hô-va phán dạy họ.
- LEV 27:29 expected `Đức Giê-hô-va`: Mọi thứ bị rủa bởi người nào không được phép chuộc lại; nó phải bị giết chết.
- NUM 2:5 expected `Giu-đa`: Chi phái Y-sa-ca phải đóng trại bên cạnh; quan trưởng của con cháu Y-sa-ca là Na-tha-na-ên, con trai Xu-a.
- NUM 2:24 expected `Eùp-ra-im`: Tất cả những người được điểm danh theo trại quân Ép-ra-im, theo các đạo quân của họ, là một trăm ngàn tám ngàn một trăm người; họ sẽ đi thứ ba.
- NUM 3:16 expected `Lê-vi`: Môi-se bèn điểm danh họ theo mạng của Đức Giê-hô-va, y như Ngài đã truyền dạy người vậy.
- NUM 4:31 expected `Mê-ra-ri`: Đây là bổn phận phải khiêng mang của họ trong mọi công việc tại hội mạc: các tấm ván của đền tạm, các thanh ngang, các trụ và các đế trụ.
- NUM 4:49 expected `Lê-vi`: Theo lệnh của Đức Giê-hô-va, Môi-se đã kiểm tra họ, mỗi người theo công việc mình và theo gánh nặng mình phải mang, theo đúng điều Đức Giê-hô-va đã truyền cho Môi-se.
- NUM 7:4 expected `Lê-vi`: Đức Giê-hô-va phán cùng Môi-se rằng:
- NUM 9:20 expected `Y-sơ-ra-ên`: Và có khi mây ở trên đền tạm vài ngày; theo lệnh Đức Giê-hô-va, người ta đóng trại, và theo lệnh Đức Giê-hô-va, người ta khởi hành.
- NUM 10:36 expected `Môi-se`: Khi rỗi, người nói: Lạy Đức Giê-hô-va, xin trở lại cùng hàng vạn ngàn ngàn người Y-sơ-ra-ên!
- NUM 12:5 expected `Môi-se`: Đức Giê-hô-va ngự xuống trong trụ mây, rồi đứng tại cửa hội mạc, và gọi A-rôn và Mi-ri-am; cả hai người ra đi.
- NUM 13:31 expected `Ca-lép`: Nhưng những người đi cùng với ông nói: Chúng ta không thể lên đánh dân ấy được, vì họ mạnh hơn chúng ta.
- NUM 16:19 expected `A-rôn`: Cô-rê nhóm cả hội chúng lại nghịch cùng người, đến trước cửa nhà hội; và vinh hiển của Đức Giê-hô-va hiện ra trước toàn thể hội chúng.
- NUM 16:19 expected `Môi-se`: Cô-rê nhóm cả hội chúng lại nghịch cùng người, đến trước cửa nhà hội; và vinh hiển của Đức Giê-hô-va hiện ra trước toàn thể hội chúng.
- NUM 18:9 expected `Y-sơ-ra-ên`: Đây sẽ là phần thuộc về ngươi trong các vật rất thánh từ lửa: mọi lễ vật của họ, mọi của lễ chay, mọi của lễ chuộc tội, mọi của lễ chuộc sự mắc lỗi mà họ dâng lại cho Đức Giê-hô-va; các vật rất thánh nầy sẽ thuộc về n...
- NUM 18:12 expected `Y-sơ-ra-ên`: Mọi mỡ của dầu, mọi mỡ của rượu mới và lúa mì; phần đầu mùa mà họ dâng cho Đức Giê-hô-va, Ta đã ban cho ngươi.
- NUM 21:16 expected `Y-sơ-ra-ên`: Từ đó họ đến Bê-re; ấy là cái giếng mà Đức Giê-hô-va đã phán cùng Môi-se: Hãy nhóm dân sự lại, ta sẽ ban nước cho họ.
- NUM 21:19 expected `Y-sơ-ra-ên`: Từ Ma-tha-na đến Na-ha-li-ên; từ Na-ha-li-ên đến Ba-mốt.
- NUM 21:33 expected `Oùc`: Dân Y-sơ-ra-ên quay lại và lên đường về Ba-san; thì Oách, vua Ba-san, cùng toàn thể dân sự người đi ra đón chiến trận tại Eát-rê-i.
- NUM 21:35 expected `Oùc`: Dân Y-sơ-ra-ên đánh bại người, các con trai người và toàn thể dân sự người, cho đến nỗi không để lại cho người một ai; rồi họ chiếm lấy đất người.
- NUM 22:41 expected `Y-sơ-ra-ên`: Sáng hôm sau, Ba-lác dẫn Ba-la-am lên các nơi cao Ba-mốt-Ba-anh, và từ đó người thấy tận cùng dân sự.
- NUM 23:7 expected `Đông-phương`: Ba-la-am cất bài ca mình mà nói rằng: Từ A-ram, Ba-lác vua Mô-áp đã sai đón tôi, từ các núi phía Đông; hãy đến, nguyền rủa tôi Gia-cốp, và hãy đến, nổi giận cùng Y-sơ-ra-ên.
- NUM 23:14 expected `Ba-la-am`: Người dẫn người đến đồng Xô-phim, trên đỉnh núi Phích-ga, và người xây bảy bàn thờ, rồi dâng lên mỗi bàn thờ một con bò đực và một con chiên đực.
- NUM 23:17 expected `Ba-la-am`: Người đến cùng người, và nầy, người đứng trên của lễ thiêu của mình, và các quan trưởng Mô-áp ở cùng người. Ba-lác nói cùng người rằng: Đức Giê-hô-va đã phán chi?
- NUM 23:18 expected `Ba-la-am`: Vậy người cất lời mình lên và nói rằng: Hỡi Ba-lác, hãy chỗi dậy mà nghe! Hỡi Ba-lác, con trai Xếp-bô, hãy lắng tai mà nghe!
- NUM 26:3 expected `Y-sơ-ra-ên`: Môi-se và thầy tế lễ Ê-lê-a-sa nói cùng họ tại các đồng bằng Mô-áp bên bờ sông Giô-đanh đối ngang Giê-ri-cô, rằng:
- NUM 28:3 expected `Y-sơ-ra-ên`: Vậy, ngươi phải nói cùng họ rằng: Đây là của lễ thiêu dùng lửa mà các ngươi sẽ dâng cho Đức Giê-hô-va: mỗi ngày hai chiên con đực một tuổi, không tật, làm của lễ thiêu hằng hiến.
- NUM 32:19 expected `Y-sơ-ra-ên`: Vì chúng tôi sẽ không được hưởng phần cùng họ bên kia sông Giô-đanh và xa hơn, vì phần sản nghiệp của chúng tôi đã về chúng tôi bên này sông Giô-đanh về phía đông.
- NUM 32:33 expected `Oùc`: Vậy Môi-se ban cho con cháu của Ru-bên, con cháu của Gát và phân nửa chi phái Ma-na-se con trai của Giô-sép, làm sản nghiệp là vương quốc của Si-hôn vua dân A-mô-rít và vương quốc của Ôg vua Ba-san, tức là xứ ấy với c...
