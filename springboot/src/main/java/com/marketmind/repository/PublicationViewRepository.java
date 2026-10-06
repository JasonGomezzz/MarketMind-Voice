package com.marketmind.repository;

import com.marketmind.entity.PublicationView;
import org.springframework.data.repository.Repository;

import java.util.Collection;
import java.util.List;

/** Solo lectura: Spring Data no expone save ni delete en esta interfaz. */
public interface PublicationViewRepository extends Repository<PublicationView, Long> {

    List<PublicationView> findByCampaignIdIn(Collection<Long> campaignIds);
}
